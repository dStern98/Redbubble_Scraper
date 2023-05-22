import json
import os
from pathlib import Path

from .download_images import DownloadImages
from .redbubble_scraper import ScrapeRedbubble
from .config import SETTINGS
from .schemas import ScraperResults
from .utils import block_for_user_input


def load_config_json() -> list[str]:
    path_to_config_json = Path(os.path.dirname(__file__)) / "config.json"

    # # Load the config file
    with open(path_to_config_json, "r") as file:
        search_list: list[str] = json.load(file)

    if not search_list:
        search_list = [
            "almost famous poster",
            "stranger things poster",
            "seinfeld poster",
            "star wars poster"
        ]

    return search_list


async def main():
    """
    The main function first calls the Scrape_Redbubble class, which opens a browser, 
    and performs the necessary web scraping. The web scraping results are then passed into the 
    Download_Images class, which uses HTTPX to gather all of the pictures.
    """
    search_list = load_config_json()

    search_results_dict = ScrapeRedbubble.scrape_images(
        search_list,
        max_search_result_size=SETTINGS.MAX_ITEMS_PER_SCRAPE)
    scrape_results = ScraperResults(results=search_results_dict)

    if SETTINGS.DEBUG_MODE:
        print("Scrape Complete...")
        block_for_user_input()

    await DownloadImages(
        scrape_results=scrape_results,
        batch_size=SETTINGS.BATCH_SIZE).download_files()
