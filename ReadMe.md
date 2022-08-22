# About

This is a Redbubble Scraper. It uses Selenium to open up a browser, search for a
set of desired results. It will then download the first 15-16 images for each search,
placing the downloaded files into a folder named `Scraped_Images`.
The `Scraped_Images` folder will have subfolders named for the inputed search result. For example, if the search term was `star trek poster`, then the subfolder name would be `star_trek_poster`.
The actual `.jpg` file name will be a concatenation of the image name, author, and price on Redbubble.

Under the hood, the Selenium scraper reads the `src` property for each `<img>` tag in the search results. The images for a given search are all then requested asyncronously using `HTTPX` and `asyncio.gather`. The response bytes are then written to the OS
as described above using the PIL module. A helpful file called `search_results.json` is always created after running the scraper.
This file contains all of the metadata for each search required for the HTTPX requests. `search_results.json` is never read by the code, it is purely for convenience and book keeping. An example `search_results.json` and corresponding `config.json` file has been pushed to Github.

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

Then, just run the command `python main.py`.
Note that while the code will automatically download a Chrome Driver, it will not automatically download Chrome, so make sure Chrome is installed on your computer before running.
