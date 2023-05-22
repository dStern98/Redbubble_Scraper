import requests
import time


def block_for_user_input():
    """
    Allow a user to allow the program to continue.
    """
    print("-" * 75)
    user_res = input(
        "Would you like to continue execution of the program (Y/N)?")

    if user_res.strip().lower() not in ["yes", "y"]:
        print("Exiting program on user's request")
        quit()


def wait_for_remote_container():
    """
    Unfortunately, despite the depends_on in the docker-compose, sometimes the scraper begins before 
    remote webdriver is up and ready. Test periodically for the connection.
    """
    print("Waiting for remote container connection...")
    iterations = 0
    while iterations < 20:
        try:
            res = requests.get("http://selenium_remote_webdriver:4444")
            if res.status_code == 200:
                print("Remote Webdriver connection successful!")
                time.sleep(1)
                return
        except Exception:
            time.sleep(3)
            iterations += 1
    raise RuntimeError(
        "Unable to connect to webdriver after 20 tries.")
