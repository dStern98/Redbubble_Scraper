import os
import asyncio
import httpx
from pathlib import Path
import aiofiles
import re

from .schemas import ScraperResults, ImageMetadata

STRING_SANITIZE_PATTERN = re.compile(r"[^\s\w]")

PATH_TO_IMAGE_FOLDER = Path(os.path.dirname(
    __file__)) / ".." / "Scraped_Images"
if not PATH_TO_IMAGE_FOLDER.is_dir():
    PATH_TO_IMAGE_FOLDER.mkdir()


class DownloadImages:
    """
    Class to download the images using HTTPX, and write the image 
    bytes to the OS.
    """

    def __init__(
            self,
            scrape_results: ScraperResults,
            batch_size: int = 5):
        """
        scrape_results_dicts: The results of the Selenium Scraper, passed
        as a Pydantic Class for better type integrity.
        batch_size: How many Images should be requested from Redbubble at once. 
        Be very mindful of getting flagged for a DDOS attack if this is set too high!
        """
        self.scrape_results_dict = scrape_results.results
        self.batch_size = batch_size if batch_size < 50 and batch_size > 0 else 5

    @staticmethod
    def sanitize_string(string: str, repl: str = "_") -> str:
        """
        Remove any non-alphanumeric characters from the author/titles,
        as these will likely cause an OS exception for an invalid filename.
        """
        return re.sub(
            pattern=STRING_SANITIZE_PATTERN,
            string=string,
            repl=repl)

    async def _request_and_download_image(
            self,
            dir_to_write_to: Path,
            image_metadata: ImageMetadata):
        """
        Given the search term and scraped image metadata, request the image
        from Redbubble, then write the image to the underlying OS.
        """
        async with httpx.AsyncClient() as client:
            res = await client.get(
                url=image_metadata.url,
                timeout=15.0
            )
        res.raise_for_status()

        # Build the file_basename, and write to the OS.
        title = self.sanitize_string(image_metadata.title)
        author = self.sanitize_string(image_metadata.author)
        extension = image_metadata.url.split('.')[-1]

        async with aiofiles.open(
                dir_to_write_to / f"{title}_{author}.{extension}",
                "wb") as file:
            await file.write(res.content)

    @staticmethod
    def print_exceptions(outcomes: list):
        """
        Exceptions in the asyncio.gather are returned. 
        print any exceptions out.
        """
        for outcome in outcomes:
            if isinstance(outcome, Exception):
                print(f"Exception {outcome} generated during download")

    @staticmethod
    def build_search_folder(search_name: str) -> Path:
        """
        Scraped Images are written in a subdirectory of `Scraped_Images`
        with the same name as the search term used for the scrape, with spaces replaced 
        by underscores. Create this subdir if required.
        Return the full path to the subdir.
        """
        # First, create the search_name folder if it does not exist
        path_to_search_folder = (
            PATH_TO_IMAGE_FOLDER / search_name.replace(" ", "_"))

        if not path_to_search_folder.is_dir():
            path_to_search_folder.mkdir()

        return path_to_search_folder

    async def download_files(self):
        """
        Make the HTTPX Requests to get the images.
        """
        print("-" * 75)
        print("Begginning Image Download...")
        for search_name, search_results in self.scrape_results_dict.items():
            path_to_search_folder = self.build_search_folder(
                search_name=search_name)
            print(f"Downloading images for => {search_name}")
            # In batches of the batch size, download the images.
            lower = 0
            while metadata_to_download := search_results[lower: lower + self.batch_size]:
                download_outcomes = await asyncio.gather(
                    *(self._request_and_download_image(
                        dir_to_write_to=path_to_search_folder,
                        image_metadata=image_metadata) for image_metadata in metadata_to_download
                      ),
                    return_exceptions=True
                )
                self.print_exceptions(download_outcomes)
                lower += self.batch_size
