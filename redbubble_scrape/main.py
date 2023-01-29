from .scraper.redbubble_scraper import ScrapeRedbubble
from .scraper.download_images import DownloadImages
import json
import os
import glob
from typing import List

# Load the config file
with open(os.path.join(os.path.dirname(__file__), "config.json"), "r") as file:
    search_list: List = json.load(file)


def print_download_summary():
    """
    Convenient Print Summary, especially useful when deployed in Docker.
    """
    path_to_scraped_images = os.path.join(
        os.path.dirname(__file__), "..", "Scraped_Images")
    list_of_subdirectores = os.listdir(path_to_scraped_images)
    for subdir in list_of_subdirectores:
        number_of_jpegs = glob.glob(os.path.join(
            path_to_scraped_images, subdir, "*.jpg"))
        print(f"Got {len(number_of_jpegs)} images for {subdir}")


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
        search_list, max_search_result_size=40)

    await DownloadImages(search_results_dict).download_files()

    print_download_summary()
