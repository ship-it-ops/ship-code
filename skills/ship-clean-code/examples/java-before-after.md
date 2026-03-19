# Java: Before & After

## Scenario
A user notification service that loads user preferences, selects a delivery
channel, formats the message, and dispatches it.

---

## Before (8 violations)

```java
public class NotificationService {

    private String dbUrl;
    private String dbUser;
    private String dbPass;
    private String smtpHost;
    private String smtpPort;
    private String smtpUser;
    private String smtpPass;
    private String templateDir;

    // 8-argument constructor
    public NotificationService(String dbUrl, String dbUser, String dbPass,
            String smtpHost, String smtpPort, String smtpUser,
            String smtpPass, String templateDir) {
        this.dbUrl = dbUrl;
        this.dbUser = dbUser;
        this.dbPass = dbPass;
        this.smtpHost = smtpHost;
        this.smtpPort = smtpPort;
        this.smtpUser = smtpUser;
        this.smtpPass = smtpPass;
        this.templateDir = templateDir;
    }

    // Boolean flag controls behavior
    public void send(String userId, String message, int channel,
                     boolean isUrgent) {
        try {
            // 1 = email, 2 = sms, 3 = push
            Connection conn = DriverManager.getConnection(dbUrl, dbUser, dbPass);
            PreparedStatement ps = conn.prepareStatement(
                "SELECT * FROM users WHERE id = ?");
            ps.setString(1, userId);
            ResultSet rs = ps.executeQuery();

            if (rs.next()) {
                String email = rs.getString("email");
                String phone = rs.getString("phone");
                String token = rs.getString("push_token");

                String formatted;
                if (isUrgent) {
                    formatted = "[URGENT] " + message;
                } else {
                    formatted = message;
                }

                if (channel == 1) {
                    sendEmail(email, formatted, isUrgent);
                } else if (channel == 2) {
                    sendSms(phone, formatted);
                } else if (channel == 3) {
                    sendPush(token, formatted);
                }
            }

            conn.close();
        } catch (Exception e) {
            System.out.println("Error: " + e.getMessage());
        }
    }

    // Static method that depends on instance state conceptually
    public static String formatForChannel(String msg, int channel) {
        if (channel == 1) return "<html><body>" + msg + "</body></html>";
        if (channel == 2 && msg.length() > 160)
            return msg.substring(0, 157) + "...";
        return msg;
    }

    public static UserPreference findPref(String id) {
        // returns null when not found
        return null;
    }

    private void sendEmail(String to, String msg, boolean urgent) { }
    private void sendSms(String to, String msg) { }
    private void sendPush(String token, String msg) { }
}

// Value object without equals/hashCode
class UserPreference {
    private String userId;
    private int preferredChannel;

    public UserPreference(String userId, int preferredChannel) {
        this.userId = userId;
        this.preferredChannel = preferredChannel;
    }

    public String getUserId() { return userId; }
    public int getPreferredChannel() { return preferredChannel; }
}
```

---

## After (Corrected)

```java
import java.util.Objects;
import java.util.Optional;

// [5] Raw integers replaced with an enum
public enum NotificationChannel {
    EMAIL, SMS, PUSH
}

// ---- Configuration objects replace long constructor arg lists ---- [1]

public record DatabaseConfig(
    String url,
    String user,
    String password
) { }

public record SmtpConfig(
    String host,
    int port,
    String user,
    String password
) { }

// [8] Value object with proper equals/hashCode via record
public record UserPreference(
    String userId,
    NotificationChannel preferredChannel
) { }
// Records auto-generate equals, hashCode, and toString.

// ---- Formatting is an instance concern, not static ---- [2]

public interface MessageFormatter {
    String format(String message, NotificationChannel channel);
}

public class DefaultMessageFormatter implements MessageFormatter {

    private static final int SMS_MAX_LENGTH = 160;     // [5] Named constant
    private static final String SMS_ELLIPSIS = "...";

    @Override
    public String format(String message, NotificationChannel channel) {
        return switch (channel) {
            case EMAIL -> "<html><body>" + message + "</body></html>";
            case SMS   -> truncateForSms(message);
            case PUSH  -> message;
        };
    }

    private String truncateForSms(String message) {
        if (message.length() <= SMS_MAX_LENGTH) {
            return message;
        }
        return message.substring(0, SMS_MAX_LENGTH - SMS_ELLIPSIS.length())
               + SMS_ELLIPSIS;
    }
}

// ---- Urgency is a type, not a boolean flag ---- [6]

public enum Urgency {
    NORMAL, URGENT
}

// ---- Repository handles data access separately ---- [8b]

public class UserRepository {

    private final DatabaseConfig dbConfig;

    public UserRepository(DatabaseConfig dbConfig) {
        this.dbConfig = dbConfig;
    }

    public Optional<UserContact> findContactById(  // [4] Optional, not null
        String userId
    ) {
        try (var conn = DriverManager.getConnection(
                dbConfig.url(), dbConfig.user(), dbConfig.password());
             var ps = conn.prepareStatement(
                "SELECT email, phone, push_token FROM users WHERE id = ?")) {

            ps.setString(1, userId);
            try (var rs = ps.executeQuery()) {      // [3] try-with-resources
                if (rs.next()) {
                    return Optional.of(new UserContact(
                        rs.getString("email"),
                        rs.getString("phone"),
                        rs.getString("push_token")
                    ));
                }
            }
        } catch (SQLException e) {                  // [3] Specific exception
            throw new DataAccessException(
                "Failed to load contact for user " + userId, e);
        }
        return Optional.empty();
    }

    public Optional<UserPreference> findPreference(String userId) {
        // ... similar pattern, returns Optional.empty() if absent
        return Optional.empty();                     // [4] Never returns null
    }
}

public record UserContact(String email, String phone, String pushToken) { }

// ---- Service class ---- [1] Constructor takes 3 focused collaborators

public class NotificationService {

    private final UserRepository userRepository;
    private final MessageFormatter formatter;
    private final NotificationDispatcher dispatcher;

    public NotificationService(                      // [1] 3 args, not 8
        UserRepository userRepository,
        MessageFormatter formatter,
        NotificationDispatcher dispatcher
    ) {
        this.userRepository = userRepository;
        this.formatter = formatter;
        this.dispatcher = dispatcher;
    }

    public void send(                                // [6] Enum, not boolean
        String userId,
        String message,
        NotificationChannel channel,                 // [5] Enum, not int
        Urgency urgency
    ) {
        UserContact contact = userRepository
            .findContactById(userId)
            .orElseThrow(() -> new UserNotFoundException(userId));

        String body = applyUrgencyPrefix(message, urgency);
        String formatted = formatter.format(body, channel);

        dispatcher.dispatch(contact, channel, formatted);
    }

    private String applyUrgencyPrefix(              // [8b] Single abstraction
        String message, Urgency urgency
    ) {
        return urgency == Urgency.URGENT
            ? "[URGENT] " + message
            : message;
    }
}

// Dispatcher hides channel-specific logic behind one interface
public interface NotificationDispatcher {
    void dispatch(UserContact contact,
                  NotificationChannel channel,
                  String formattedMessage);
}
```

---

## Annotations

| # | Violation (Before) | Fix (After) |
|---|---|---|
| 1 | **Too many constructor arguments (8)** -- `dbUrl`, `dbUser`, `dbPass`, `smtpHost`, `smtpPort`, `smtpUser`, `smtpPass`, `templateDir` | Grouped into `DatabaseConfig` and `SmtpConfig` records; service constructor takes 3 collaborators |
| 2 | **Static utility method** -- `formatForChannel` is static but logically belongs to an instance | Extracted to `MessageFormatter` interface with `DefaultMessageFormatter` implementation |
| 3 | **Catching `Exception` broadly** -- `catch (Exception e)` masks bugs; resources not closed properly | Catches `SQLException` specifically; uses try-with-resources for `Connection`, `PreparedStatement`, `ResultSet` |
| 4 | **Returning null** -- `findPref` returns `null` when user not found | Returns `Optional<UserPreference>` and `Optional<UserContact>`; callers use `orElseThrow` |
| 5 | **Raw integer constants** -- `1 = email, 2 = sms, 3 = push`, `160` for SMS limit | Replaced with `NotificationChannel` enum and `SMS_MAX_LENGTH` named constant |
| 6 | **Boolean flag argument** -- `boolean isUrgent` changes method behavior | Replaced with `Urgency` enum; intent is explicit at the call site |
| 7 | **Missing equals/hashCode on value object** -- `UserPreference` class has no structural equality | Converted to a Java `record`, which auto-generates `equals`, `hashCode`, and `toString` |
| 8 | **Long method with mixed abstraction levels** -- `send()` opens DB connections, formats messages, and dispatches in one block | Split into `UserRepository` (data access), `MessageFormatter` (formatting), `NotificationDispatcher` (delivery), and a thin orchestrating `send()` method |
