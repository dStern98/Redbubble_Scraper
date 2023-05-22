from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromiumService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from pathlib import Path
import json
import os
import time

from .utils import wait_for_remote_container
from .config import SETTINGS


class MaxScrapeCountReached(Exception):
    """
    Communicates that a scrape operation
    has reached the max count.
    """
    ...


class MissingImageMetadata(Exception):
    """
    Communicates that a scrape operation
    could not find the required metadata.
    """
    ...


class ScrapeRedbubble:
    """
    The Scrape_Redbubble class takes an array of search terms from the config.json file.
    It iterates over the array, puts the search term into the Redbubble search bar, 
    and records the desired number of results.
    """

    @classmethod
    def set_bot_driver(cls):
        """
        Set-up the Selenium Driver for usage. 

        There are really 3 possible deployment configurations:
        1. Selenium Webdriver is downloaded onto the machine running this python script.
        2. Selenium Webdriver is accessed via a Docker Image, but this python script
        executes directly on the host OS.
        3. Both Selenium and this python script execute in two docker images configured to talk
        to each other via a network (this would be ideal for an automated cloud deployment).
        """
        # Disable Selenium logging, as it is uneccessary and confusing
        options = Options()
        options.add_experimental_option(
            'excludeSwitches', ['enable-logging'])

        # If we are using a Remote Webdriver, the driver is set as such
        if SETTINGS.USE_REMOTE_WEBDRIVER:
            # If this UI_Bot is running in a container, then we cannot talk
            # to the remote_webdriver via localhost. Otherwise, use the name of the container
            # internally (see the docker-compose.yaml file.)
            remote_webdriver_url = (
                'http://localhost:4444' if not SETTINGS.PYTHON_RUNNING_IN_CONTAINER
                else "http://selenium_remote_webdriver:4444")
            print("Using the remote webdriver...")
            driver = webdriver.Remote(
                command_executor=remote_webdriver_url,
                options=options)
        else:
            print("Using the local webdriver...")
            driver = webdriver.Chrome(
                service=ChromiumService(
                    ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
                options=options)

        driver.implicitly_wait(15)
        cls.driver = driver

    @classmethod
    def open_redbubble(cls):
        """
        Navigates to redbubble.com and maximizes the window.
        """
        cls.driver.get("https://www.redbubble.com/")
        cls.driver.maximize_window()

    def __init__(
            self,
            search_input: str,
            search_size_max: int):
        """
        search_input: The string being search in the Redbubble search bar
        scraped_image_metadata: A list of all of the content from the scraper
        search_size_max: the max number of image metadata to scrape for the given search term
        """
        self.search_input = search_input
        self.scraped_image_metadata = []
        self.search_size_max = search_size_max

    def _find_image_urls(self,
                         a_tag_element: WebElement) -> list:
        """
        Given the Parent a_tag element of a single poster/image, 
        iterate over the child <img/> tags, and try to find one whose
        src property ends with .jpg.
        """
        return [web_element.get_property(
                "src") for web_element in a_tag_element.find_elements(
                By.TAG_NAME, "img") if web_element.get_property(
                "src").endswith(".jpg")]

    def _enter_search_term_into_searchbar(self):
        """
        Enter the search into the search bar and press enter
        """
        search_box = self.driver.find_element(
            By.CSS_SELECTOR, "input[placeholder='Search designs and products']")
        search_box.clear()
        search_box.send_keys(self.search_input + Keys.ENTER)

    def _get_image_url(
            self,
            a_tag_element: WebElement) -> list[str]:
        """
        Returns a list that should either have 1 item in it, being the image URL, 
        or be empty. 

        To solve for the issue where not all images are rendered until they are 
        visible in the browser, we scroll down to cause the image to render, 
        if no .jpg src exists within the a_tag_element.
        """
        image_urls = self._find_image_urls(a_tag_element)
        if not image_urls:
            # Scroll the window down to cause images to render
            self.driver.execute_script(
                f"window.scrollTo(0, {a_tag_element.rect['y']});")
            for _ in range(5):
                # To avoid any rendering race conditions, we loop 5 times
                # if we cannot find the .jpg src immediately
                image_urls = self._find_image_urls(a_tag_element)
                if image_urls:
                    break
                else:
                    time.sleep(0.1)
        return image_urls

    def _get_grid_of_a_tags(self) -> list[WebElement]:
        """
        All of the Posters/Images are contained beneath a single parent <div/>
        with ID 'SearchResultsGrid'. Each individual image/poster element
        has an <a/> as its parent. Return the list of <a/> elements that 
        are children of the SearchResultsGrid <div/>.
        """
        # First, get the single parent div of all the search results
        search_results_parent_div = self.driver.find_element(
            By.ID, "SearchResultsGrid")
        # Second, get the list of <a> tags beneath the parent div
        return search_results_parent_div.find_elements(
            By.TAG_NAME, "a")

    def _handle_pop_up(self, attempt: int):
        """
        Sometimes, a Redbubble Pop-up disrupts the loop. Handle this.

        Refresh the page to eliminate the pop-up, and recursively
        calls _scrape_current_page_metadata -> It is recursive because this
        method _handle_pop_up is called from inside of _scrape_current_page_metadata.
        """
        if attempt < 3:
            self.driver.refresh()
            time.sleep(0.5)
            self._scrape_current_page_metadata(attempt=attempt)
        else:
            raise MissingImageMetadata(
                "Unable to find required metadata after 3 attempts.")

    def _find_image_metadata_in_a_tag(self, a_tag: WebElement) -> dict | None:
        """
        Given the parent <a/> representing a single image/poster element, 
        try to find the desired metadata: image_url, title, author, and price.
        """
        # Get the image_urls
        possible_image_url = self._get_image_url(a_tag)
        # Get the price
        price = a_tag.find_element(By.CSS_SELECTOR, "span>span").text
        # Get the poster name and author
        poster_name_and_author = [span_web_element.text for span_web_element in a_tag.find_elements(
            By.TAG_NAME, "span") if (span_web_element.text and "$" not in span_web_element.text)]

        if all((len(poster_name_and_author) == 2, price, possible_image_url)):
            poster_name, poster_author = poster_name_and_author
            return {
                "title": poster_name,
                "url": possible_image_url[0],
                "price": price,
                "author": poster_author
            }

    def _scrape_current_page_metadata(self, attempt=0):
        """
        Scrape the Current Page's metadata.

        If during the loop the max items is acquired, 
        MaxScrapeCountReached Exception is raised.
        """
        grid_of_parent_a_tags = self._get_grid_of_a_tags()
        this_page_scraped_metadata = []
        for a_tag in grid_of_parent_a_tags:

            if len(self.scraped_image_metadata) + len(this_page_scraped_metadata) >= self.search_size_max:
                self.scraped_image_metadata.extend(this_page_scraped_metadata)
                raise MaxScrapeCountReached(
                    f"Scrape for {self.search_input} reached max size.")

            if parsed_metadata := self._find_image_metadata_in_a_tag(a_tag):
                this_page_scraped_metadata.append(parsed_metadata)
            elif attempt == 0:
                # If this block is entered, this most likely means
                # that a Redbubble Pop-up is blocking further HTML interaction
                self._handle_pop_up(attempt=attempt + 1)
                return
            else:
                # After the first attempt, we assume that this is not a pop-up issue.
                # Ignore the <a/> in question and move on to the next one.
                continue
        self.scraped_image_metadata.extend(this_page_scraped_metadata)

    def _move_to_next_page(self):
        """
        Click the Next Page if Required.

        Unfortunately, there is not an easy identifer of the necessary <a/>. It is a direct
        child of a <span/>, and there is a child <Strong/> tag of the a_tag with the text 'Next' in it.
        """
        possible_next_a_tags = [element for element in self.driver.find_elements(By.CSS_SELECTOR, "span>a")
                                if element.get_attribute("class").startswith("Pagination")]

        # One of the next_a_tags in the possible_next_a_tags array is the one we want.
        for possible_next_a_tag in possible_next_a_tags:
            if child_strong_elements := possible_next_a_tag.find_elements(By.TAG_NAME, "strong"):
                if child_strong_elements.pop().text == "Next":
                    # If the a_tag has a <strong/> child with text "Next",
                    # click on it.
                    possible_next_a_tag.click()
                    # Give the Browser time to load the next page
                    # or you can get a stale element exception.
                    time.sleep(0.75)
                    return

        raise RuntimeError("Unable to click next page...")

    def search_and_scrape_pictures(self) -> list[dict[str, str]]:
        """
        Performs all of the necessary scraping operations for a single 
        search term.
        """
        try:
            self._enter_search_term_into_searchbar()
            # Iterate over the a tags and get the img src, price and general info
            while True:
                try:
                    self._scrape_current_page_metadata()
                    self._move_to_next_page()
                except MaxScrapeCountReached:
                    break
        finally:
            self.driver.get("https://www.redbubble.com/")
            print(
                f"{self.search_input} => got {len(self.scraped_image_metadata)} items from scrape")
            return self.scraped_image_metadata

    @staticmethod
    def write_results_to_json(scrape_results: dict):
        """
        Write the Results to file search_results.json for debugging 
        and also in case further analysis is desired.
        """
        json_file_path = Path(os.path.dirname(
            __file__)) / ".." / "search_results.json"
        with open(json_file_path, "w") as file:
            json.dump(scrape_results, file, indent=2)

    @classmethod
    def scrape_images(
            cls,
            search_list: list[str],
            max_search_result_size: int = 15) -> dict:
        """
        Class Method that runs the scraper for the given set of search terms.
        """
        print("-" * 75)
        scrape_results = {}
        # If Running in Container, make sure the remote webdriver is up
        if SETTINGS.PYTHON_RUNNING_IN_CONTAINER and SETTINGS.USE_REMOTE_WEBDRIVER:
            wait_for_remote_container()

        cls.set_bot_driver()
        cls.open_redbubble()

        # Get the Image Urls and associated metadata
        for search_term in search_list:
            try:
                scrape_results[search_term] = cls(
                    search_input=search_term,
                    search_size_max=max_search_result_size).search_and_scrape_pictures()
            except Exception as exc:
                print(f"Uncaught exception: {exc} for: {search_term}")

        cls.driver.quit()
        cls.write_results_to_json(scrape_results)
        return scrape_results


if __name__ == "__main__":
    scraped_responses = ScrapeRedbubble.scrape_images(
        search_list=[
            "almost famous poster",
            "stranger things poster",
            "seinfeld poster",
            "star wars poster"
        ],
        max_search_result_size=200
    )
