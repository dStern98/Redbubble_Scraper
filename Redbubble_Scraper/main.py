from Scraper_Implementation.redbubble_scraper import Scrape_Redbubble
from Scraper_Implementation.download_images import Download_Images
import json
import os
from typing import List
import asyncio

# Load the config file
with open(os.path.join(os.path.dirname(__file__), "config.json"), "r") as file:
    search_list: List = json.load(file)


async def main():
    """
    The main function first calls the Scrape_Redbubble class, which opens a browser, 
    and performs the necessary web scraping. The web scraping results are then passed into the 
    Download_Images class, which uses HTTPX to gather all of the pictures.
    """

    if len(search_list) == 0:
        raise Exception(
            "The passed array from config.json is empty. Please put desired search criteria in.")

    search_results_dict = Scrape_Redbubble.scrape_images(search_list)
    await Download_Images(search_results_dict).download_files()


if __name__ == "__main__":
    asyncio.run(main())
