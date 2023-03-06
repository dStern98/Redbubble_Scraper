import requests
import time
import os
import glob


def wait_for_remote_container():
    """
    Unfortunately, despite the depends_on in the docker-compose, sometimes the scraper begins before 
    remote webdriver is up and ready. Test periodically for the connection.
    """
    print("Waiting for remote container connection...")
    iterations = 0
    while True:
        try:
            res = requests.get("http://selenium_remote_webdriver:4444")
            if res.status_code == 200:
                print("Remote Webdriver connection successful!")
                time.sleep(1)
                break
        except Exception:
            if iterations > 20:
                raise Exception(
                    "Unable to connect to remove webdriver after 20 tries.")
            else:
                time.sleep(3)
                iterations += 1


def print_download_summary():
    """
    Convenient Print Summary, especially useful when deployed in Docker.
    """
    path_to_scraped_images = os.path.join(
        os.path.dirname(__file__),
        "..",
        "Scraped_Images"
    )
    list_of_subdirectores = os.listdir(path_to_scraped_images)

    # Print the number of jpg files found per directory
    for subdir in list_of_subdirectores:
        number_of_jpegs = glob.glob(os.path.join(
            path_to_scraped_images, subdir,
            "*.jpg"))
        print(f"Got {len(number_of_jpegs)} images for {subdir}")
