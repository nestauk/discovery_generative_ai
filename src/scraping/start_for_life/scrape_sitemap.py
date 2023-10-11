"""
Get all URLs from the NHS https://www.nhs.uk/start-for-life/site-map/

Usage:

First navigate to the scraping folder
$ cd src/scraping/start_for_life

Then run the script
$ poetry run python scrape_sitemap.py

The final output file is stored in data/sitemap.csv
with the following columns:
    - Title: Title of the page
    - URL: URL of the page

"""
import csv
import logging

import requests

from bs4 import BeautifulSoup


# Headers to be used when scraping
HEADERS = {
    "User-Agent": "Data collection for the purpose of research. For questions, reach out to karlis.kanders@nesta.org.uk"
}

# URL with the website you want to scrape
BASE_URL = "https://www.nhs.uk/start-for-life/site-map/"
# Path to your output CSV file with titles and URLs
OUTPUT_PATH = "data/sitemap.csv"


def scrape_urls(base_url: str, csv_filename: str, timeout: float = 10) -> None:
    """
    Get all URLs from a website and save them to a CSV file

    Args:
        base_url:
            URL of the website to scrape

        csv_filename:
            Path to the CSV file to save the URLs to

        timeout:
            Timeout in seconds for the request to the website
    """

    # Create a set to hold Titles and URLs
    unique_urls = []
    url_titles = []
    # Make a request to the website
    response = requests.get(
        base_url,
        timeout=timeout,
        headers=HEADERS,
    )
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content of the page using Beautiful Soup
        soup = BeautifulSoup(response.text, "html.parser")
        # Find all anchor tags (<a>) in the HTML
        for link in soup.find_all("a"):
            # Get the href attribute (the URL)
            url = link.get("href")
            # Check if the URL starts with 'http' or 'https' to ignore relative URLs
            if url and (url.startswith("http") or url.startswith("https") or url.startswith("/")):
                unique_urls.append(url)
                if type(link.text) is str:
                    url_titles.append(link.text.strip())
                else:
                    url_titles.append("")

    # Write the unique URLs to a CSV file
    with open(csv_filename, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Title", "URL"])  # Header row

        for i, url in enumerate(unique_urls):
            csv_writer.writerow([url_titles[i], url])

    logging.info(f"Scraping complete. {len(unique_urls)} unique URLs have been saved to {csv_filename}.")


if __name__ == "__main__":
    scrape_urls(BASE_URL, OUTPUT_PATH)
