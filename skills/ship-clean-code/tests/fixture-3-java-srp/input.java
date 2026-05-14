import java.sql.*;
import java.util.*;

public class OrderManager {

    public void createOrder(int customerId, List<Integer> productIds, double total, boolean isPremium) {
        try {
            Connection conn = DriverManager.getConnection("jdbc:mysql://localhost/shop", "root", "password");
            Statement stmt = conn.createStatement();

            stmt.executeUpdate("INSERT INTO orders (customer_id, total) VALUES (" + customerId + ", " + total + ")");

            for (Integer pid : productIds) {
                stmt.executeUpdate("INSERT INTO order_items (order_id, product_id) VALUES (LAST_INSERT_ID(), " + pid + ")");
            }

            String html = "<html><body><h1>Order Confirmed</h1><p>Total: $" + total + "</p></body></html>";

            Properties props = new Properties();
            props.put("mail.smtp.host", "smtp.example.com");
            javax.mail.Session session = javax.mail.Session.getInstance(props);
            javax.mail.Message msg = new javax.mail.internet.MimeMessage(session);
            msg.setContent(html, "text/html");
            javax.mail.Transport.send(msg);

            System.out.println("Order created for customer " + customerId);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
