import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
import mysql.connector
import mysql

if __name__ == "__main__":
    cnx = mysql.connector.connect(
        user='root', password='*',
        host='192.168.1.30',
        database='vetfeed')
    
    cursor = cnx.cursor(dictionary=True, buffered=True)


    driver = uc.Chrome()

    animals = ["kedi", "kopek"]

    for animal in animals:

        URL = f"https://www.akakce.com/{animal}-mamasi.html"
        driver.get(URL)
        page_count_element = driver.find_element(By.XPATH, "/html/body/div[2]/p/b")

        page_count = 0

        page_count_text = page_count_element.text
        page_count_text.replace("Sayfa: ", "")
        page_count_text.replace(" ", "")
        page_count = int(page_count_text.split("/")[1])

        print("PAGE_COUNT:", page_count)

        pages = [f"https://www.akakce.com/{animal}-mamasi.html"]
        for count in range(2, page_count + 1):
            pages.append(f"https://www.akakce.com/{animal}-mamasi,{count}.html")

        all_products = []
        link_count = 0
        for url in pages:
            driver.get(url)
            time.sleep(2)
            products_list = driver.find_element(By.XPATH, '//*[@id="CPL"]')
            list_items = products_list.find_elements(By.CLASS_NAME, "w")

            for list_item in list_items:
                link = list_item.find_element(By.CLASS_NAME, "pw_v8").get_attribute("href")
                print(link)
                if not link.startswith("https://www.akakce.com/c/"):
                    cursor.execute(f"INSERT INTO feed_urls VALUES ('{link}')")
                    link_count += 1
                else:
                    print("Link is outside link")
        print(link_count)
    cursor.close()
    cnx.commit()
    cnx.close()
    driver.close()
