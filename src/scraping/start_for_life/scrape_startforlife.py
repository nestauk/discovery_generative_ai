"""
Get content from all URLs from the NHS https://www.nhs.uk/start-for-life/site-map/

Usage:

First navigate to the scraping folder
$ cd src/scraping/start_for_life

Then run the script
$ poetry run python scrape_startforlife.py

The final output file is stored in data/startforlife.csv
with the following columns:
    - URL: URL of the page
    - content_type: Content type (ie, class tag of the div section)
    - header: Header of the page's section
    - content: Content of the page's section
    - content_no: Index of the section (ie, if there are multiple sections on the page, this is the integer index of the section)

"""

import logging

from time import sleep
from typing import List

import pandas as pd
import requests

from bs4 import BeautifulSoup
from tqdm import tqdm


# URLs to scrape
SITEMAP_PATH = "data/sitemap.csv"
BASE_URL = "https://www.nhs.uk/"
# Headers to be used when scraping
REQUEST_HEADERS = {
    "User-Agent": "Data collection for the purpose of research. For questions, reach out to karlis.kanders@nesta.org.uk"
}
# We're only fetching on type of div section; one can also add 'nhsuk-promo__content' to capture the site navigation content
DIV_CLASS = ["nhsuk-u-reading-width"]
# Typical header tags
HEADER_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6"]
# Sections with these header will be excluded from the final output
EXCLUDED_HEADERS = ["Sign up for emails"]
# Path to the output file
OUTPUT_PATH = "data/start_for_life.csv"


def merge_sections_based_on_headers(headers: List[str], sections: List[str]) -> (List[str], List[str], List[int]):
    """
    Merge sections based on headers, where sections without headers will be merged in the previous section that has a header

    Args:
        headers
            List of headers

        sections
            List of sections

    Returns:
        Tuple of lists with headers, merged sections and removed indices
    """
    new_headers = []
    new_sections = []
    # Keep track of removed indices
    removed_indices = []
    # Keep track of the last non-empty header index
    last_non_empty_index = -1

    for i in range(len(headers)):
        # If header is non-empty
        if headers[i]:
            new_headers.append(headers[i])
            new_sections.append(sections[i])
            last_non_empty_index = len(new_headers) - 1
        # If header is empty
        else:
            # Add index to removed list
            removed_indices.append(i)
            # If there was a previous non-empty header
            if last_non_empty_index != -1:
                new_sections[last_non_empty_index] += sections[i]

    return new_headers, new_sections, removed_indices


def web_scraper(url: str, timeout: float = 10) -> (List[str], List[str], List[str]):
    """Scrape a web page and return the content

    Args:
        url
            URL of the web page

        timeout
            Timeout in seconds for the request to the website

    Returns:
        Tuple of lists with sections' headers, content under each header and the sections' classes
    """
    # Fetch webpage
    response = requests.get(
        url,
        timeout=timeout,
        headers=REQUEST_HEADERS,
    )

    # Parse with BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    # Get all divs with the specified list of class names
    divs = soup.find_all("div", class_=DIV_CLASS)

    # Get all header (h1, h2 etc) tags from each of the divs
    headers = [[d.get_text() for d in div.find_all(HEADER_TAGS)] for div in divs]

    # Process the div content: remove headers (h1, h2, etc)
    divs_processed = []
    for div in divs:
        div_processed = div
        for header in div_processed.find_all(HEADER_TAGS):
            header.decompose()
        divs_processed.append(div_processed)
    # Get class names of the divs
    divs_classes = [div.get("class") for div in divs]
    # Keep only text
    divs_processed = [div.get_text() for div in divs_processed]
    # Merge divs without header into previous div
    headers, divs_processed, removed_indices = merge_sections_based_on_headers(headers, divs_processed)
    # Remove corresponding elements from divs_classes
    divs_classes = [div for i, div in enumerate(divs_classes) if i not in removed_indices]
    # Remove new lines from the beginning and end of each div
    divs_processed = [div.strip() for div in divs_processed]
    # and replace multiple new lines with a space
    divs_processed = [div.strip().replace("\n", " ") for div in divs_processed]
    return headers, divs_processed, divs_classes


def has_multiple_items(items: List[str]) -> bool:
    """Check if there are multiple headers in the second-level list"""
    for item in items:
        if len(item) > 1:
            logging.info(f"Multiple headers in {item}")
            return False
        else:
            return True


if __name__ == "__main__":
    sitemap_df = pd.read_csv(SITEMAP_PATH)
    content_dfs = []
    # Go through each URL and scrape the content
    for url in tqdm(sitemap_df["URL"].to_list()):
        headers, content, div_classes = web_scraper(BASE_URL + url)
        # Just checking the unlikely case of multiple headers in a div section
        has_multiple_items(headers)
        # Join lists of lists into a single list (unlikely that there is more than one header in a div class)
        headers = [". ".join(h) for h in headers]
        div_classes = ["; ".join(d) for d in div_classes]
        # Append to the list of dataframes
        content_dfs.append(
            pd.DataFrame(
                {
                    "URL": url,
                    "content_type": div_classes,
                    "header": headers,
                    "content": content,
                    "content_no": range(len(content)),
                }
            )
        )
        sleep(0.1)
    content_dfs = pd.concat(content_dfs, ignore_index=True)

    # Some light post-processing
    content_processed_df = (
        content_dfs
        # Remove rows with empty content
        .loc[content_dfs["content"].str.len() > 0]
        # Remove rows with excluded headers
        .loc[~content_dfs["header"].isin(EXCLUDED_HEADERS)]
        # For each unique URL, reindex the content_no to follow subsequent integers
        .assign(content_no=lambda x: x.groupby("URL")["content_no"].rank(method="first").astype(int))
        # Export to CSV
        .to_csv(OUTPUT_PATH, index=False)
    )
