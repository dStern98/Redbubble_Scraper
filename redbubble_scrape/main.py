from .scraper.redbubble_scraper import ScrapeRedbubble
from .scraper.download_images import DownloadImages
from .scraper.utils import print_download_summary
import json
import os

# Load the config file
with open(os.path.join(os.path.dirname(__file__), "config.json"), "r") as file:
    search_list: list[str] = json.load(file)


async def main():
    """
    The main function first calls the Scrape_Redbubble class, which opens a browser, 
    and performs the necessary web scraping. The web scraping results are then passed into the 
    Download_Images class, which uses HTTPX to gather all of the pictures.
    """

    if not search_list:
        raise Exception(
            "The passed array from config.json is empty. Please put desired search criteria in.")

    search_results_dict = ScrapeRedbubble.scrape_images(
        search_list,
        max_search_result_size=40)

    await DownloadImages(search_results_dict).download_files()

    print_download_summary()
