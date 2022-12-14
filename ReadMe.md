# About

This is a Redbubble Scraper. It uses Selenium to open up a browser, search for a
set of desired results. It will then download the desired number of images for each search,
placing the downloaded files into a folder named `Scraped_Images`.
The `Scraped_Images` folder will have subfolders named for the inputed search result. For example, if the search term was `star trek poster`, then the subfolder name would be `star_trek_poster`.
The actual `.jpg` file name will be a concatenation of the image name, author, and price on Redbubble, where the price
is formatted as dollars_cents rather than dollars.cents.

Under the hood, the Selenium scraper reads the `src` property for each `<img>` tag in the search results. The images for a given search are all then requested asyncronously using `HTTPX` and `asyncio.gather`. The response bytes are then written to the OS
as described above using the PIL module. A helpful file called `search_results.json` is always created after running the scraper.
This file contains all of the metadata for each search required for the HTTPX requests. `search_results.json` is never read by the code, it is purely for convenience and book keeping.

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

# Note on Number of Downloads

As the code is currently written, the results are iterated over, with the loop breaking when
the code fails to find the next `src` attribute in an `<img>` tag with extension `.jpg`. Because Redbubble
dynamically renders the images as the user scrolls down the page, the code automatically scrolls each `<a>` into
view if it cannot immediately find the `.jpg` source. There is a known issue where a Redbubble popup prematurely causes the
loop to exit. This issue may be fixed in future code changes.
An optional parameter `max_search_result_size`, for the `Scrape_Redbubble` classmethod `scrape_images` allows the maximum download
size per search term to be set. Its default value is 40.

# Deploy using Docker for Remote Webdriver but Python Locally

The Scraper can be run using Docker, with the `selenium/hub` image. See [here](https://github.com/SeleniumHQ/docker-selenium#dev-and-beta-standalone-mode) for the Github README (The Docker hub docs are nonexistent). When running the remote webdriver, set `use_remote_webdriver` in the `.env` to `True`. If using
a remote_webdriver, make sure a remote_webdriver has been created. The default remote_webdriver port is `4444`.
Use the command:

```
docker run -d -p 4444:4444 --shm-size="2g" selenium/standalone-chrome:4.5.0-20220929
```

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
