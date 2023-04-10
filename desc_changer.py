import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
import mysql.connector
import mysql
from platform import system

def get_full_product_title(driver: uc.Chrome):
    try:
        return driver.find_element(By.XPATH, "/html/body/main/div[1]/div/div[1]/h1").text
    except NoSuchElementException:
        return "unknown title"

if __name__ == "__main__":

    if system() == "Windows":
        cnx = mysql.connector.connect(
            user='root', password='*',
            host='192.168.1.30',
            database='vetfeed')
    else:
        cnx = mysql.connector.connect(
            user='root', password='*',
            host='localhost',
            database='vetfeed')
        
    cursor = cnx.cursor(dictionary=True, buffered=True)

    cursor.execute("SELECT product_url FROM packaging where description = 'unknown' ")
    unknown_desc_urls = [row['product_url'] for row in cursor.fetchall()]

    driver = uc.Chrome()

    for prod_url in unknown_desc_urls:
        driver.get(prod_url)
        print("GETTING URL")
        print(prod_url)
        time.sleep(5)

        title = get_full_product_title(driver)
        title = title.replace(r"'", r"\'").replace(r'"', r'\"')
        print(title)
        cursor.execute(f"""
        UPDATE packaging
        SET description = "{title}"
        WHERE product_url = "{prod_url}"
        """)
        cnx.commit()

    cursor.close()
    cnx.commit()
    cnx.close()
    driver.close()