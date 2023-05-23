# About

This is a Redbubble Scraper. It uses `selenium` to open up a browser and search for a
set of desired results. It will then download the desired number of images for each search,
placing the downloaded files into a folder named `Scraped_Images`.
The `Scraped_Images` folder will have subfolders named for the inputed search result. For example, if the search term was `star trek poster`, then the subfolder name would be `star_trek_poster`.
The actual `.jpg` file name will be a concatenation of the image title, and author.

Under the hood, the Selenium scraper reads the `src` property for each `<img>` tag in the search results. The images for a given search are all then requested asyncronously using `HTTPX` and written to the OS using `aiofiles`.

A helpful file called `search_results.json` is always created after running the scraper.
This file contains all of the metadata for each search required for the download process.
`search_results.json` is never read by the code for downloading, it is purely for convenience and book keeping.

# Directions

To use, open the file `config.json`, and write into the array
a set of desired search strings. An example `config.json` file is shown below:

```JSON
[
"almost famous poster",
"star wars poster",
"inglourious basterds poster",
"fight club poster"
]
```

Then, just run the command `python -m Redbubble_Scraper`.

# Scraper Process

The scraper consists of 2 parts:

1. The Scraper Portion: Uses Selenium to open a browser,
   navigate to Redbubble, and iterate over the list of search terms. For each search term, the author, title, price, and url of the image is gathered. The code will continue on to
   the next page as many times as required until the `MAX_ITEMS_PER_SCRAPE` threshold is reached. Redbubble advertisement pop-ups are handled by this scraper by refreshing the page and restarting the current page's scrape. A pop-up is detected when a specific `<a/>` is not displayed. The scraper process generates a `dict[str, list]` which maps each search term
   to a list of image metadata.

2. The Download portion:
   The dictionary produced in step 1 is parsed, and the images are requested from the scraped URL property using `HTTPX`. Assuming the request is successful, the
   bytes are asyncronously written to the OS using `aiofiles`. The `BATCH_SIZE` environment variable
   controls how many images are downloaded at once.

# Environment Variables

All environment variables for the scraper are optionally read by Pydantic, but have
default values. The pydantic Settings class is the following:

```
class Settings(BaseSettings):
    PYTHON_RUNNING_IN_CONTAINER: bool = False
    USE_REMOTE_WEBDRIVER: bool = False
    MAX_ITEMS_PER_SCRAPE: int = 20
    BATCH_SIZE: int = 5
    DEBUG_MODE: bool = False
```

### PYTHON_RUNNING_IN_CONTAINER:

Default is False. Indicates that the python process is running in a container.

### USE_REMOTE_WEBDRIVER:

Default is False. Indicates that a remote
webdriver should be used for scraping. This is advantageous
if running this code deployed to the cloud.

### MAX_ITEMS_PER_SCRAPE:

Default is 20. How many images should be downloaded
per search term?

### BATCH_SIZE:

Default is 5. During asyncronous downloading, how many downloads should be done at once? Note that setting this too
high could lead a server to suspect a DDOS attack.

### DEBUG_MODE:

Default is False. If True, the user is prompted after the
scraping is completed to choose whether or not to continue
with the download. This is helpful if you are not as interested in
downloading the images, and would rather just get the `search_results.json`.

# Deploy using Docker for Remote Webdriver but Python Locally

The Scraper can be run using Docker, with the `selenium/hub` image. See [here](https://github.com/SeleniumHQ/docker-selenium#dev-and-beta-standalone-mode) for the Github README (The Docker hub docs are nonexistent). When running the remote webdriver, set `USE_REMOTE_WEBDRIVER` in the `.env` to `True`. If using
a remote_webdriver, make sure a remote_webdriver has been created. The default remote_webdriver port is `4444`.
Use the command:

```
docker run -d -p 4444:4444 --shm-size="2g" selenium/standalone-chrome:4.5.0-20220929
```

Note that there is likely a much newer image than
`20220929`. Feel free to use a newer one.
Then simply run the normal start command `python -m Redbubble_Scraper`.
When running python locally but a remote webdriver in Docker, the images are downloaded to the local OS as expected.

# Deploy using Docker for both Remote Webdriver and Python

If you would like everything to run in a container, you can use docker compose.
Simply run the command:

```
docker compose -f docker-compose.yaml up -d
```

In the docker compose case, environmental variables are automatically set from the compose file.
Because the python process runs in a container, the images are downloaded to a container that would otherwise be lost
when the container shuts down. I have added a volume called `scraped_images`. This will persist the images once the container is destroyed.
