# A knowledge base for testing a parenting chatbot

You can use `scrape_sitemap.py` and `scrape_startforlife.py` scripts to collect trusted information and advice about raising a child from the [NHS Start for Life](https://www.nhs.uk/start-for-life/) website

## Usage

### Getting the sitemap URLs

First navigate to the scraping folder from repo's root
```
cd src/scraping/start_for_life
```

Then run the script
```
poetry run python scrape_sitemap.py
```

This will create a file in `data/sitemap.csv` with the following columns:
 - Title: Title of the page
 - URL: URL of the page

### Getting the text content

After fetching the sitemap URLs, run the following script
```
poetry run python scrape_startforlife.py
```

The final output file will be stored in `data/startforlife.csv` with the following columns:
  - URL: URL of the page
  - content_type: Content type (ie, class tag of the div section)
  - header: Header of the page's section
  - content: Content of the page's section
  - content_no: Index of the section (ie, if there are multiple sections on the page, this is the integer index of the section)
