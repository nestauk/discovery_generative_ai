"""
Get text data from the BBC's Tiny Happy People website about kids activities

Usage:

First navigate to the scraping folder
$ cd src/scraping/activities

Then run the script
$ poetry run python scrape_activities.py

The final output file is stored in data/tiny_happy_people - final.csv
with the following columns:
    - CONTENT: Title of the activity
    - SHORT DESCRIPTION: Short description of the activity
    - Age Range (if applicable): Age range of the activity
    - Type: Type of the activity (there are 20+ different types used by BBC)
    - URL: URL of the activity
    - text: Scraped text, describing the activity in greater detail

"""

import csv
import logging

from pathlib import Path
from time import sleep

import bs4
import pandas as pd
import requests

from bs4 import BeautifulSoup
from tqdm import tqdm


# URLs to scrape
URL_PATH = Path("data/tiny_happy_people_urls - links.csv")
# Interim file to store the scraped text
SCRAPED_PATH = URL_PATH.parent / "tiny_happy_people - scraped.csv"
# File to store the final table
OUTPUTS_PATH = URL_PATH.parent / "tiny_happy_people - final.csv"

# Possible headers signalling the end of the article
END_MARKERS = [
    "In case you missed it",
    "Find another activity",
]

# Boilerplate text to be removed
SCRAP_TEXT = [
    "TwitterFacebookMessengerWhatsAppShareShare this withTwitterFacebookMessengerWhatsAppCopy linkRead more about sharing",
    "previousnext",
]

# Headers to be used when scraping
HEADERS = {
    "User-Agent": "Data collection for the purpose of research. For questions, reach out to karlis.kanders@nesta.org.uk"
}


def pad_element(element: bs4.element.Tag) -> str:
    """Pad an element's content with spaces for certain tags (a recursive function)

    Args:
        element (bs4.element.Tag): HTML element

    Returns:
        str: Text with spaces
    """
    if isinstance(element, str):
        return element
    elif element.name in ["p", "h1", "h2", "h3", "h4", "h5", "h6"]:
        return " " + " ".join(pad_element(child) for child in element.children) + " "
    else:
        return "".join(pad_element(child) for child in element.children)


# Function to scrape the web page
def web_scraper(url: str, timeout: float = 10) -> str:
    """Scrape a web page and return the content

    Args:
        url
            URL of the web page

    Returns:
        Dataframe with URL and content
    """
    # Fetch webpage
    response = requests.get(
        url,
        timeout=timeout,
        headers=HEADERS,
    )

    # Parse with BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    # Remove all <style>...</style> tags
    for style_tag in soup.find_all("style"):
        style_tag.extract()

    # Find the headline
    headline = soup.find("h1", class_="blocks-article__headline")

    # Fetch all the content starting from headline
    content = []
    curr_element = headline.find_next_sibling()
    while curr_element is not None:
        content.append(curr_element)
        curr_element = curr_element.find_next_sibling()

    # Clean the text from HTML tags and add spaces
    clean_content = "".join(pad_element(element) for element in content)

    # Remove the end of the webpage
    if any(marker in clean_content for marker in END_MARKERS):
        for marker in END_MARKERS:
            clean_content = clean_content.split(marker)[0]

    # Remove the boilerplate text
    for text in SCRAP_TEXT:
        clean_content = clean_content.replace(text, "")

    return clean_content.strip()


if __name__ == "__main__":
    urls_df = pd.read_csv(URL_PATH)

    # Fetch the already scraped urls
    if SCRAPED_PATH.exists():
        scraped_urls = pd.read_csv(SCRAPED_PATH, names=["URL", "text"]).URL.to_list()
    else:
        scraped_urls = []

    new_urls_df = urls_df[~urls_df["URL"].isin(scraped_urls)]

    # Scrape the urls
    with open(SCRAPED_PATH, "a") as f:
        writer = csv.writer(f)
        for row in tqdm(new_urls_df.itertuples(), total=len(new_urls_df)):
            try:
                # if url starts with 'www' then add 'https://'
                url = "https://" + row.URL if row.URL.startswith("www") else row.URL
                text = web_scraper(url)
                writer.writerow([row.URL, text])
            except Exception:
                logging.warning(f"Error scraping {row.URL}")
            sleep(0.5)

    # Create the final output table
    final_df = urls_df.merge(
        pd.read_csv(SCRAPED_PATH, names=["URL", "text"]),
        on="URL",
        how="left",
    )
    final_df.to_csv(OUTPUTS_PATH, index=False)
