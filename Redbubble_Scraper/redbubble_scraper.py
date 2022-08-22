from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromiumService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import json


class Scrape_Redbubble:
    """
    The Scrape_Redbubble class takes an array of search terms from the config.json file.
    It iterates over the array, puts the search term into the Redbubble search bar, 
    and records first 15-16 results.
    """

    def __init__(self):
        self.driver = webdriver.Chrome(service=ChromiumService(
            ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()))
        self.driver.implicitly_wait(15)

    def open_redbubble(self):
        self.driver.get("https://www.redbubble.com/")
        self.driver.maximize_window()

    def search_and_scrape_pictures(self, search_input: str) -> dict:

        # Enter the search into the search bar and press enter
        search_box = self.driver.find_element(
            By.CSS_SELECTOR, "input[placeholder='Search designs and products']")
        search_box.clear()
        search_box.send_keys(search_input + Keys.ENTER)

        # First, get the single parent div of all the search results
        search_results_parent_div = self.driver.find_element(
            By.ID, "SearchResultsGrid")

        # Second, get the list of <a> tags beneath the parent div
        list_of_a_tags = search_results_parent_div.find_elements(
            By.TAG_NAME, "a")

        array_of_img_metadata = []

        # Third, iterate over the a tags and get the img src, price and general info
        for a_tag in list_of_a_tags:

            # Get the image urls
            list_of_image_urls = [web_element.get_property(
                "src") for web_element in a_tag.find_elements(
                By.TAG_NAME, "img") if web_element.get_property(
                "src").endswith(".jpg")]

            # Get the price
            price = a_tag.find_element(
                By.CSS_SELECTOR, "span>span").text

            # Get the poster name and author
            list_of_descriptors = [span_web_element.text for span_web_element in a_tag.find_elements(
                By.TAG_NAME, "span") if (span_web_element.text and "$" not in span_web_element.text)]

            if all([len(list_of_descriptors) > 0, price, len(list_of_image_urls) > 0]):
                array_of_img_metadata.append(
                    {"title": f"{'_'.join(list_of_descriptors)}_{price}", "url": list_of_image_urls[0]})

            # Redbubble only downloads a subset of the available posters to the browser. The rest is dynamically
            # requested for as the user scrolls down the page. Once the loop reaches this point where
            # the desired data is missing for a set of a tags, break.
            if any([len(list_of_descriptors) == 0, len(list_of_image_urls) == 0, price is None]):
                break

        self.driver.get("https://www.redbubble.com/")

        return array_of_img_metadata

    @classmethod
    def scrape_images(cls, search_list: list[str]):
        search_results_dict = {}

        # Create a Class Instance
        redbubble_scraper = cls()

        # Open Redbubble
        redbubble_scraper.open_redbubble()

        # Get the Image Urls and associated metadata
        for search_term in search_list:
            search_results_dict["_".join(search_term.split(" "))] = redbubble_scraper.search_and_scrape_pictures(
                search_term)

        with open("search_results.json", "w") as file:
            json.dump(search_results_dict, file, indent=2)

        return search_results_dict
