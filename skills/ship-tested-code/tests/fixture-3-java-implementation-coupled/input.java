import org.junit.jupiter.api.Test;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class DiscountCalculatorTest {

    @Test
    void test1() throws Exception {
        WebDriver driver = new ChromeDriver();
        driver.get("http://localhost:8080/cart");
        driver.findElement(By.id("add-item")).click();
        Thread.sleep(1000);
        driver.findElement(By.id("apply-coupon")).click();
        driver.findElement(By.id("coupon-input")).sendKeys("SAVE10");
        driver.findElement(By.id("submit")).click();
        Thread.sleep(2000);
        String text = driver.findElement(By.id("total")).getText();
        assertEquals("90.00", text);
        driver.quit();
    }

    @Test
    void testCalcInternal() {
        DiscountCalculator calc = new DiscountCalculator();

        DiscountCalculator spy = spy(calc);
        spy.apply(100.0, "SAVE10");

        verify(spy).lookupCouponInDatabase("SAVE10");
        verify(spy).multiplyByRate(100.0, 0.9);
    }
}
