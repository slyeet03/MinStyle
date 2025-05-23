import time
import util
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def search(query, driver):
    """
    Searches for a given query on Westside and extracts product details.
    """
    url = f"https://www.westside.com/pages/search?q={query.replace(' ', '%20')}"

    try:
        driver.get(url)
        time.sleep(1)
        # Wait for product containers to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".wizzy-result-product"))
        )

        # Scroll down multiple times to load more products
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

        # Wait for lazy-loaded images to load
        WebDriverWait(driver, 10).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, "img[data-src], img[src]")
        )

        # Small extra wait to ensure images load fully
        time.sleep(2)

        soup = bs(driver.page_source, "html.parser")
        product_containers = soup.find_all("li", class_="wizzy-result-product")[:5]

        if not product_containers:
            util.log("No results found on Westside.")
            return None, None, None, None, None

        return extract_product_data(product_containers)

    except Exception as e:
        util.log(f"Error in search function: {e}")
        return None, None, None, None, None


def extract_product_data(product_containers):
    """
    Extracts product data from Westside's HTML.
    """
    base_url = "https://www.westside.com"
    names, prices, links, images, brands = [], [], [], [], []

    try:
        for product in product_containers:
            # Get product name and brand
            name_tag = product.find("p", class_="product-item-title")
            brand_tag = product.find("p", class_="product-item-sub-title")
            product_name = name_tag.text.strip() if name_tag else "No Name"
            brand = brand_tag.text.strip() if brand_tag else "No Brand"
            names.append(product_name)
            brands.append(brand)

            # Get price
            price_tag = product.find("div", class_="wizzy-product-item-price")
            price = price_tag.text.strip() if price_tag else "N/A"
            prices.append(price)

            # Get product link
            link_tag = product.find("a", class_="wizzy-result-product-item")
            product_link = (
                base_url + link_tag["href"] if link_tag and link_tag.get("href") else "No Link"
            )
            links.append(product_link)

            # Improved image extraction - only look within current product container
            img_tag = product.find("img")
            image_url = "No Image"
            
            if img_tag:
                # Check data-src first (common for lazy-loaded images)
                if img_tag.get("data-src"):
                    image_url = img_tag["data-src"]
                # Then check srcset
                elif img_tag.get("srcset"):
                    srcset = img_tag["srcset"]
                    # Get the highest resolution image from srcset
                    image_url = srcset.split(",")[-1].split()[0]
                # Finally check regular src
                elif img_tag.get("src"):
                    image_url = img_tag["src"]
            
            images.append(image_url)

        return names, prices, links, images, brands

    except Exception as e:
        util.log(f"Error in extract_product_data: {e}")
        return None, None, None, None, None