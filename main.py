import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
import mysql.connector
import mysql
from platform import system

def get_brand(driver: uc.Chrome):
    try:
        return driver.find_element(By.XPATH, "/html/body/main/div[1]/div/div[1]/a[1]").get_property("title")
    except NoSuchElementException:
        return get_full_product_title(driver)

def get_full_product_title(driver: uc.Chrome):
    try:
        return driver.find_element(By.XPATH, "/html/body/main/div[1]/div/div[1]/h1").text
    except NoSuchElementException:
        return "unknown title"


def get_product_image_link(driver: uc.Chrome):
    return driver.find_element(By.XPATH, "/html/body/main/div[1]/div/div[2]/a/img").get_attribute("src")

def get_weight_from_info(product_info):
    if "Ağırlık" in product_info.keys():
        return product_info["Ağırlık"]
    else:
        return None

def get_weight_from_description(description: str) -> float:
    try:
        words = description.lower().split(" ")
        if "kg" in words:
            kg_index = words.index("kg")
            if kg_index == -1:
                return -1
            return float(words[kg_index - 1].replace(",", "."))
        else:
            return -1
    except Exception as e:
        print("Error while getting weight from description!")
        print(e)
        return -1

def get_price(driver: uc.Chrome):
    try:
        raw_price_text = driver.find_element(By.CSS_SELECTOR, "span.pb_v8:nth-child(2) > span:nth-child(1)").text
        return float(raw_price_text.lower().replace("tl", "").strip().replace(".", "").replace(",", "."))
    except NoSuchElementException:
        try:
            full_text = driver.find_element(By.XPATH, "/html/body/main/div[1]/div/p[2]/span[1]/span[2]").text
            price_per_kg_text = driver.find_element(By.XPATH, "/html/body/main/div[1]/div/p[2]/span[1]/span[2]/span").text
            raw_price_text = full_text.replace(price_per_kg_text, "").lower().replace("tl", "").strip().replace(".", "").replace(",", ".")
            return float(raw_price_text)
        except NoSuchElementException:
            return -1



def get_species(driver: uc.Chrome):
    if "kedi-mamasi" in driver.current_url:
        return "kedi"
    elif "kopek-mamasi" in driver.current_url:
        return "kopek"
    else:
        return "unknown"


def get_species_id(cursor, species: str):
    cursor.execute(f"""
        SELECT id FROM animal_species
        WHERE species = '{species}'
        """)
    return cursor.fetchone()['id']


def get_rating_avg(driver: uc.Chrome):
    try:
        rating_avg = driver.find_element(By.CSS_SELECTOR, ".scw_v9 > i:nth-child(3)")
        return float(rating_avg.text)
    except NoSuchElementException:
        print("rating avg cannot be found")
        return -1
    
def get_rating_count(driver: uc.Chrome):
    try:
        rating_count = driver.find_element(By.CSS_SELECTOR, ".scw_v9 > b:nth-child(4)").text
        return int(rating_count.replace(" kişi oyladı", "").strip())
    except NoSuchElementException:
        print("rating count cannot be found")
        return -1


def get_packaging_options(driver: uc.Chrome):
    option_urls = []
    try:
        options_list = driver.find_element(By.XPATH, '//*[@id="PRG_v8"]')
        options = options_list.find_elements(By.TAG_NAME, "li")
        for option in options:
            print(option.text)
            option_url = option.find_element(By.TAG_NAME, "a").get_attribute("href")
            option_urls.append(option_url)
        return option_urls
    except NoSuchElementException:
        print("get_packaging_options cannot be found! returning current url")
        return [driver.current_url]

def get_product_specs(driver: uc.Chrome) -> tuple:
    try:
        a = {}
        b = []
        tables_div = driver.find_element(By.CSS_SELECTOR, "#DT_w")
        tables = tables_div.find_elements(By.TAG_NAME, "table")
        for table in tables:
            trs = table.find_elements(By.TAG_NAME, "tr")
            for tr in trs:
                tds = tr.find_elements(By.TAG_NAME, "td")
                field = tds[0].text
                desc = tds[1].text
                if desc.replace(":", "") == "":
                    b.append(field)
                    continue
                desc = desc.replace(":", "").strip()
                a[field] = desc
        return a, b
    except NoSuchElementException:
        print("Product specs are not listed!")
        return {}, []

def add_brand(cursor , brand_name) -> int:
    cursor.execute(f"""
    SELECT id FROM brands
    WHERE name = "{brand_name}"
    """)
    already_exists = cursor.fetchone()
    if already_exists:
        return already_exists["id"]

    cursor.execute(f"""
    INSERT INTO brands (name)
    VALUES ("{brand_name}")
    """)
    return cursor.lastrowid

def add_specs(cursor, feed_id, specs: list):
    for spec_name in specs:
        spec_id = None
        cursor.execute(f"""
        SELECT id FROM spec_names
        WHERE name = '{spec_name}'
        """)
        already_exists = cursor.fetchone()
        if already_exists:
            spec_id = already_exists["id"]
        else:
            cursor.execute(f"""
            INSERT INTO spec_names (name)
            VALUES ("{spec_name}")
            """)
            spec_id = cursor.lastrowid



        cursor.execute(f"""
        SELECT feed_id, spec_id FROM specs
        WHERE feed_id = {feed_id} AND spec_id = {spec_id}
        """)
        already_exists = cursor.fetchone()
        if already_exists:
            return
        else:
            cursor.execute(f"""
            INSERT INTO specs (feed_id, spec_id)
            VALUES ({feed_id}, {spec_id})
            """)

def get_age(cursor, info_dict: dict) -> int:
    if 'Yaş' in info_dict.keys():
        cursor.execute(f"""
        SELECT id FROM ages
        WHERE age = '{info_dict['Yaş']}'
        """)
        already_exists = cursor.fetchone()
        if already_exists:
            return already_exists["id"]

        cursor.execute(f"""
        INSERT INTO ages (age)
        VALUES ('{info_dict['Yaş']}')
        """)
        return cursor.lastrowid
    else:
        cursor.execute(f"""
        SELECT id FROM ages
        WHERE age = 'unknown'
        """)
        return cursor.fetchone()['id']


def get_breed(cursor, info_dict: dict, animal_species: int) -> int:
    if 'Irk' in info_dict.keys():
        cursor.execute(f"""
        SELECT id FROM breeds
        WHERE breed = '{info_dict['Irk']}' AND animal_species = {animal_species}
        """)
        already_exists = cursor.fetchone()
        if already_exists:
            return already_exists["id"]

        cursor.execute(f"""
        INSERT INTO breeds (animal_species, breed)
        VALUES ({animal_species}, "{info_dict['Irk']}")
        """)
        return cursor.lastrowid
    else:
        cursor.execute(f"""
        SELECT id FROM breeds
        WHERE breed = 'unknown' AND animal_species = {animal_species}
        """)
        return cursor.fetchone()['id']
    

def get_flavor(cursor, info_dict: dict) -> int:
    if 'Aroma' in info_dict.keys():
        cursor.execute(f"""
        SELECT id FROM flavors
        WHERE flavor = '{info_dict['Aroma']}'
        """)
        already_exists = cursor.fetchone()
        if already_exists:
            return already_exists["id"]

        cursor.execute(f"""
        INSERT INTO flavors (flavor)
        VALUES ('{info_dict['Aroma']}')
        """)
        return cursor.lastrowid
    else:
        cursor.execute(f"""
        SELECT id FROM flavors
        WHERE flavor = 'unknown'
        """)
        return cursor.fetchone()['id']
    

def get_kibble_size(cursor, info_dict: dict) -> int:
    if 'Tane Boyutu' in info_dict.keys():
        cursor.execute(f"""
        SELECT id FROM kibble_sizes
        WHERE size_name = '{info_dict['Tane Boyutu']}'
        """)
        already_exists = cursor.fetchone()
        if already_exists:
            return already_exists["id"]

        cursor.execute(f"""
        INSERT INTO kibble_sizes (size_name)
        VALUES ('{info_dict['Tane Boyutu']}')
        """)
        return cursor.lastrowid
    else:
        cursor.execute(f"""
        SELECT id FROM kibble_sizes
        WHERE size_name = 'unknown'
        """)
        return cursor.fetchone()['id']

def add_feed(cursor, brand_name, animal_type, info_dict, driver) -> int:
    brand_id = add_brand(cursor, brand_name)
    species_id = get_species_id(cursor, get_species(driver))
    age_id = get_age(cursor, info_dict)
    breed_id = get_breed(cursor, info_dict, species_id)
    flavor_id = get_flavor(cursor, info_dict)
    kibble_size_id = get_kibble_size(cursor, info_dict)

    cursor.execute(f"""
    INSERT INTO feeds (brand_id, species_id, age_id, breed_id, flavor_id, kibble_size_id)
    VALUES ({brand_id}, {species_id}, {age_id}, {breed_id}, {flavor_id}, {kibble_size_id})
    """)
    return cursor.lastrowid


def add_packaging_to_feed(cursor, driver, feed_id, info):
    brand_id = add_brand(cursor, get_brand(driver))
    description = get_full_product_title(driver)
    weight = get_weight_from_description(description)
    price = get_price(driver)
    rating_avg = get_rating_avg(driver)
    rating_count = get_rating_count(driver)
    image_url = get_product_image_link(driver)
    product_url = driver.current_url
    needs_fixing = False
    cursor.execute(f"""
        INSERT INTO packaging 
            (brand_id,
            feed_id,
            weight,
            price,
            rating_avg,
            rating_count,
            image_url,
            product_url,
            description,
            needs_fixing
            )
        VALUES (
            {brand_id},
            {feed_id},  
            {weight}, 
            {price}, 
            {rating_avg}, 
            {rating_count}, 
            '{image_url}', 
            '{product_url}', 
            "{description.replace(r"'", r"\'").replace(r'"', r'\"')}", 
            {needs_fixing}
            )
        """)
    return cursor.lastrowid
    


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

    cursor.execute("SELECT * FROM already_parsed_urls")
    already_parsed_urls = [row['url'] for row in cursor.fetchall()]

    driver = uc.Chrome()

    cursor.execute("SELECT url FROM feed_urls")
    all_urls = [row['url'] for row in cursor.fetchall()]

    for prod_url in all_urls:
        if prod_url in already_parsed_urls:
            print("PROD URL ALREADY PARSED")
            print(prod_url)
            continue
        driver.get(prod_url)
        print("GETTING URL")
        print(prod_url)
        time.sleep(5)

        fail_string = "Bu ürün için şu anda akakce.com'da listelenen satıcılarda fiyat bilgisi bulunamadı."

        if fail_string in driver.page_source:
            cursor.execute(f"""
            INSERT INTO already_parsed_urls
            VALUES ('{driver.current_url}')
            """)
            already_parsed_urls.append(driver.current_url)

        info, specs = get_product_specs(driver)
        if not info and not specs:
            print("No specs was listed!")
            cursor.execute(f"""
                INSERT INTO already_parsed_urls
                VALUES ('{driver.current_url}')
                """)
            already_parsed_urls.append(driver.current_url)
            cnx.commit()
            continue
        package_urls = get_packaging_options(driver)

        feed_id = add_feed(cursor, get_brand(driver), get_species(driver), info, driver)
        add_specs(cursor, feed_id, specs)

        # print(package_urls)
        # print(already_parsed_urls)

        for url in package_urls:
            if url in already_parsed_urls:
                print("URL ALREADY PARSED")
                print(url)
                continue

            driver.get(url)
            time.sleep(5)
            if fail_string in driver.page_source:
                cursor.execute(f"""
                INSERT INTO already_parsed_urls
                VALUES ('{driver.current_url}')
                """)
                already_parsed_urls.append(url)
                continue

            # Bu feede packaging bilgisi ekle
            info, specs = get_product_specs(driver)
            add_packaging_to_feed(cursor, driver, feed_id, info)

            cursor.execute(f"""
            INSERT INTO already_parsed_urls
            VALUES ('{url}')
            """)
            already_parsed_urls.append(url)

        if prod_url not in already_parsed_urls:
            cursor.execute(f"""
            INSERT INTO already_parsed_urls
            VALUES ('{prod_url}')
            """)
            already_parsed_urls.append(prod_url)

        cnx.commit()

    cursor.close()
    cnx.commit()
    cnx.close()
    driver.close()