from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromiumService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from .utils import wait_for_remote_container
from .config import SETTINGS
import json
import os
import time


class Scrape_Redbubble:
    """
    The Scrape_Redbubble class takes an array of search terms from the config.json file.
    It iterates over the array, puts the search term into the Redbubble search bar, 
    and records the desired number of results.
    """

    @classmethod
    def set_bot_driver(cls):

        # Disable Selenium logging, as it is uneccessary and confusing
        options = Options()
        options.add_experimental_option(
            'excludeSwitches', ['enable-logging'])

        # If this UI_Bot is running in a container, then we cannot talk
        # to the remote_webdriver via localhost. Instead, we use the name of the Container Internally
        remote_webdriver_url = (
            'http://localhost:4444' if not SETTINGS.python_running_in_container else "http://selenium_remote_webdriver:4444")

        # If we are using a Remote Webdriver, the driver is set as such
        if SETTINGS.use_remote_webdriver:
            print("Using the remote webdriver")
            driver = webdriver.Remote(
                command_executor=remote_webdriver_url,
                options=options)
        else:
            print("Using the local web driver...")
            driver = webdriver.Chrome(
                service=ChromiumService(
                    ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
                options=options)

        driver.implicitly_wait(15)
        cls.driver = driver

    @classmethod
    def open_redbubble(cls):
        cls.driver.get("https://www.redbubble.com/")
        cls.driver.maximize_window()

    @staticmethod
    def get_img_urls(a_tag_element) -> list:
        return [web_element.get_property(
                "src") for web_element in a_tag_element.find_elements(
                By.TAG_NAME, "img") if web_element.get_property(
                "src").endswith(".jpg")]

    def scroll_until_image_available(self, a_tag_element) -> list[str]:
        """
        To solve for the issue where not all images are rendered until they are 
        visible in the browser, we scroll down to cause the image to render, 
        if no .jpg src exists within the a_tag_element.
        """
        list_of_image_urls = self.get_img_urls(a_tag_element)

        if not list_of_image_urls:

            # Scroll the window down to cause images to render
            self.driver.execute_script(
                f"window.scrollTo(0, {a_tag_element.rect['y']});")

            for _ in range(5):
                # To avoid any rendering race conditions, we loop 5 times
                # if we cannot find the .jpg src immediately
                list_of_image_urls = self.get_img_urls(a_tag_element)
                if list_of_image_urls:
                    break
                else:
                    time.sleep(0.1)

        return list_of_image_urls

    def search_and_scrape_pictures(self, search_input: str, search_size_max: int) -> list[dict[str, str]]:

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
        # Third, iterate over the a tags and get the img src, price and general info
        array_of_img_metadata = []
        for a_tag in list_of_a_tags:

            if len(array_of_img_metadata) >= search_size_max:
                break

            # Get the image_urls
            list_of_image_urls = self.scroll_until_image_available(a_tag)
            # Get the price
            price = a_tag.find_element(
                By.CSS_SELECTOR, "span>span").text
            # Get the poster name and author
            list_of_descriptors = [span_web_element.text for span_web_element in a_tag.find_elements(
                By.TAG_NAME, "span") if (span_web_element.text and "$" not in span_web_element.text)]

            if all((list_of_descriptors, price, list_of_image_urls)):
                array_of_img_metadata.append(
                    {
                        "title": f"{'_'.join(list_of_descriptors)}_{price.replace('.', '_')}",
                        "url": list_of_image_urls[0]
                    }
                )
            else:
                break

        self.driver.get("https://www.redbubble.com/")

        return array_of_img_metadata

    @classmethod
    def scrape_images(cls, search_list: list[str], max_search_result_size: int = 40) -> dict:
        search_results_dict = {}
        # If Running in Container, make sure the remote webdriver is up
        if SETTINGS.python_running_in_container and SETTINGS.use_remote_webdriver:
            wait_for_remote_container()
        # Start the Driver
        cls.set_bot_driver()
        # Open Redbubble
        cls.open_redbubble()

        # Get the Image Urls and associated metadata
        for search_term in search_list:
            search_results_dict[search_term.replace(" ", "_")] = cls().search_and_scrape_pictures(
                search_term, search_size_max=max_search_result_size)

        cls.driver.quit()

        with open(os.path.join(os.path.dirname(__file__), "search_results.json"), "w") as file:
            json.dump(search_results_dict, file, indent=2)

        return search_results_dict
