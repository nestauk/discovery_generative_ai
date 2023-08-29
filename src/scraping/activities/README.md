# Examples of activities

You can use `scrape_activities.py` to collect examples of kids activities from the [Tiny Happy People website](https://www.bbc.co.uk/tiny-happy-people/activities/zjh8hbk).

The relevant urls were found in [this spreadsheet](https://docs.google.com/spreadsheets/d/1loK4_sCp35JRVM9z_xW8inF3eqb7pL-jEuFWuJ5fjNE/edit#gid=0)


## Usage

First navigate to the scraping folder from repo's root
```
cd src/scraping/activities
```

Then run the script
```
poetry run python scrape_activities.py
```

The final output table is stored in `data/tiny_happy_people - final.csv`
with the following columns:
- CONTENT: Title of the activity
- SHORT DESCRIPTION: Short description of the activity
- Age Range (if applicable): Age range of the activity
- Type: Type of the activity (there are 20+ different types used by BBC)
- URL: URL of the activity
- **text: Scraped text, describing the activity in greater detail**

## Notes

You can use `scrape_notebook.ipynb` to test the scraping function for single URLs
