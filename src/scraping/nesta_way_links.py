import asyncio
import logging
import os

from pathlib import Path
from typing import List

import aiohttp

from bs4 import BeautifulSoup as soup
from pycookiecheat import chrome_cookies


logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s", level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")

# Current preprocessing backend assumes MacOS
domain = "https://sites.google.com"
base_url = f"{domain}/u/0/d/1MBMfmeJF8D2ySUbZZ-PQgOVyiLsrhjYT/preview"
headers = {
    "User-Agent": "Data collection for the purpose of research. For questions, reach out to solomon.yu@nesta.org.uk"
}
cookies = chrome_cookies(base_url, browser="Chrome")

parsed_links = set()
parsed_links.add(base_url)


async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    """Fetch a url and return the response text."""
    async with session.get(url, headers=headers, cookies=cookies) as response:
        return await response.text()


async def parse_google_site_href(url: str, domain: str = "https://sites.google.com") -> List[str]:
    """Parse href links in a Google site url string."""
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, url)
        links = list(set([i.get("href") for i in soup(html, "html.parser").find_all("a", href=True)]))
        return [
            domain + link
            if isinstance(link, str)
            and link.startswith("/u/0/d/")  # This may break if domain or url structure changes
            else link
            for link in links
        ]


async def recursive_parse_links(
    url_or_urls: List[str],
    session: aiohttp.ClientSession,
    domain: str = "https://sites.google.com",
) -> List[str]:
    """Recursively parse unique links from a list of urls.

    Args:
        url_or_urls (Union[str, List[str]]): A single url or a list of urls.

    Returns:
        List[str]: A list of urls.
    """
    num_links_parsed = len(parsed_links)
    new_links = []

    for link in url_or_urls:
        if link.startswith(domain) and link not in parsed_links:

            # Clear the terminal window
            os.system("cls" if os.name == "nt" else "clear")  # nosec B605

            parsed_links.add(link)
            logger.info(f"Number links parsed: {len(parsed_links)}")
            new_links.extend(await parse_google_site_href(link))

    if len(parsed_links) == num_links_parsed:
        return list(parsed_links)
    else:
        return await recursive_parse_links(new_links, session)


async def main() -> None:
    """Run scraper and write links to a text file."""
    async with aiohttp.ClientSession() as session:
        links = await parse_google_site_href(base_url, domain=domain)
        final_links = await recursive_parse_links(links, session)

    try:
        write_path = Path("./data/nesta_way_links.txt")
        if not write_path.exists():
            write_path.touch()
    except FileNotFoundError as e:
        logger.warning(f"{e.strerror}, file will be created.")
    finally:
        with open(write_path, "w") as f:
            for link in final_links:
                f.write(f"{link}\n")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
