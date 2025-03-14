# Load libraries
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
from argparse import ArgumentParser
from google.cloud import bigquery
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By

# Main website for Safari browser release notes
SAFARI_RELEASE_NOTES = "https://developer.apple.com/documentation/safari-release-notes"

LIST_OF_LINKS_TO_IGNORE = []

TARGET_PROJECT = "moz-fx-data-shared-prod"
TARGET_TABLE = "moz-fx-data-shared-prod.external_derived.chrome_extensions_v1"
GCS_BUCKET = "gs://moz-fx-data-prod-external-data/"
RESULTS_FPATH = "SAFARI_RELEASE_NOTES/safari_release_notes_%s.csv"
TIMEOUT_IN_SECONDS = 10

driver = webdriver.Chrome()
driver.get(SAFARI_RELEASE_NOTES)
driver.implicitly_wait(5) 

# Extract links
links = [a.get_attribute("href") for a in driver.find_elements(By.TAG_NAME, "a")]

for link in links:
    print(link)

driver.quit()

# Function to get all unique links found on a given webpage
# def get_unique_links_from_webpage(
#     url, base_url, timeout_seconds, links_to_ignore, links_to_not_process
# ):
#     """Input: Webpage, timeout seconds (integer), links to ignore, links already processed
#     Output: List of unique, absolute links on that page"""

#     response = requests.get(url, timeout=timeout_seconds)
#     soup = BeautifulSoup(response.text, "html.parser")

#     links = [urljoin(base_url, a["href"]) for a in soup.find_all("a", href=True)]
#     unique_links = []
#     for link in links:
#         if (
#             link not in unique_links
#             and link not in links_to_ignore
#             and link not in links_to_not_process
#         ):
#             unique_links.append(link)
#     return unique_links

# Function to get the soup returned from a given page
# def get_soup_from_webpage(webpage_url, timeout_seconds):
#     """Input: Webpage URL, timeout
#     Output: BeautifulSoup class"""
#     response = requests.get(webpage_url, timeout=timeout_seconds)
#     soup_from_webpage = BeautifulSoup(response.text, "html.parser")
#     return soup_from_webpage






# Function to initialize a results dataframe
def initialize_results_df():
    """Returns a dataframe with 0 rows with the desired format"""
    results_df = pd.DataFrame(
        columns=[
            "submission_date",
            "browser_release_notes_url",
            "browser_release_date",
            "browser_version",
            "browser_major_version",
            "browser_minor_version",
            "browser_release_overview",
            "accessibility_notes",
            "browser_notes",
            "canvas_notes",
            "css_notes",
            "editing_notes",
            "network_notes",
            "pdf_notes",
            "form_notes",
            "rendering_notes",
            "security_notes",
            "svg_notes",
            "web_animation_notes",
            "web_api_notes"
        ]
    )
    return results_df


# def main():
#     parser = ArgumentParser(description=__doc__)
#     parser.add_argument("--date", required=True)
#     args = parser.parse_args()

#     # Get DAG logical date
#     logical_dag_date = datetime.strptime(args.date, "%Y-%m-%d").date()
#     logical_dag_date_string = logical_dag_date.strftime("%Y-%m-%d")

#     # Initialize a list of the non-detail page links that have already been processed
#     links_already_processed = []

#     #Get all links found on this page
#     # links_found = get_unique_links_from_webpage(url=SAFARI_RELEASE_NOTES,
#     #                                           base_url=SAFARI_RELEASE_NOTES,
#     #                                           timeout_seconds=TIMEOUT_IN_SECONDS,
#     #                                           links_to_ignore=LIST_OF_LINKS_TO_IGNORE,
#     #                                           links_to_not_process=links_already_processed)
    
#     print('links_found')
#     print(links_found)
    
#     # Initialize a dataframe to store extension level results
#     results_df = initialize_results_df()


# if __name__ == "__main__":
#     main()
