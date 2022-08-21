import os
import asyncio
import json
import httpx
from io import BytesIO
from PIL import Image
import re

remove_bad_chars = re.compile(r'\W')


class Download_Images:
    def __init__(self, search_results_dict: dict = {}):
        self.search_results_dict = search_results_dict
        self.path_to_image_folder = os.path.join(
            os.path.dirname(__file__), "..", "Scraped_Images")

        if not os.path.isdir(self.path_to_image_folder):
            os.mkdir(self.path_to_image_folder)

    @staticmethod
    def make_images(responses: list, search_results: list, path_to_search_folder: str):
        for res, search_results in zip(responses, search_results):
            if res.status_code == 200:
                file_basename: str = "_".join(remove_bad_chars.sub(
                    "", string=search_results["title"]).split(" "))

                # First, make the final_image_path for each jpg
                final_image_path = os.path.join(
                    path_to_search_folder, f"{file_basename}.jpg")

                # Read the Image Bytes and Save the following using PIL module
                if not os.path.isfile(final_image_path):
                    try:
                        Image.open(BytesIO(res.content)).save(
                            final_image_path)
                    except Exception as exc:
                        print(exc)

    async def download_files(self):
        for search_name, search_results in self.search_results_dict.items():

            # First, create the search_name folder if it does not exist
            path_to_search_folder = os.path.join(
                self.path_to_image_folder, search_name)
            if not os.path.isdir(path_to_search_folder):
                os.mkdir(path_to_search_folder)

            # Prep the url_list
            url_list = [metadata["url"] for metadata in search_results]

            # Make a set of api_requests
            async with httpx.AsyncClient() as client:
                responses = await asyncio.gather(*(client.get(url) for url in url_list))

            self.make_images(responses, search_results, path_to_search_folder)


if __name__ == "__main__":

    with open("search_results.json", "r") as file:
        search_results_dict = json.load(file)

    asyncio.run(Download_Images(search_results_dict).download_files())
