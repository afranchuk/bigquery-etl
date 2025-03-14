# Load libraries
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
from argparse import ArgumentParser
from google.cloud import bigquery
from urllib.parse import urljoin
import json

# Main website for Edge browser release notes
EDGE_RELEASE_NOTES = "https://learn.microsoft.com/en-us/deployedge/microsoft-edge-relnote-stable-channel"

LIST_OF_LINKS_TO_IGNORE = []

TARGET_PROJECT = "moz-fx-data-shared-prod"
TARGET_TABLE = "moz-fx-data-shared-prod.external_derived.chrome_extensions_v1"
GCS_BUCKET = "gs://moz-fx-data-prod-external-data/"
RESULTS_FPATH = "EDGE_RELEASE_NOTES/edge_release_notes_%s.csv"
TIMEOUT_IN_SECONDS = 10


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
def get_soup_from_webpage(webpage_url, timeout_seconds):
    """Input: Webpage URL, timeout
    Output: BeautifulSoup class"""
    response = requests.get(webpage_url, timeout=timeout_seconds)
    soup_from_webpage = BeautifulSoup(response.text, "html.parser")
    return soup_from_webpage

def get_paragraphs_from_soup(webpage_soup):
    """Input: Webpage Soup
    Output: List of paragraphs found in the soup"""
    paragraphs = [p.text for p in webpage_soup.find_all("p")]
    return paragraphs


def get_h1_headers_from_soup(webpage_soup):
    """Input: Webpage Soup
    Output: List of H1 Elements Found"""
    headers = [h1.text for h1 in webpage_soup.find_all("h1")]
    return headers

def get_li_headers_from_soup(webpage_soup):
    """Input: Webpage Soup
    Output: List of H1 Elements Found"""
    bullets = [li.text for li in webpage_soup.find_all("li")]
    return bullets


def get_h2_headers_from_soup(webpage_soup):
    """Input: Webpage Soup
    Output: List of H2 Elements Found
    """
    headers = [h2.text for h2 in webpage_soup.find_all("h2")]
    return headers

def get_h2_headers_for_versions_from_soup(webpage_soup):
    """Input: Webpage Soup
    Output: List of H2 Elements Found
    """
    headers = [h2 for h2 in webpage_soup.find_all("h2")]
    headers_that_start_with_version = []
    for header in headers:
        if header.text.startswith("Version "):
          headers_that_start_with_version.append(header)
    return headers_that_start_with_version

def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    args = parser.parse_args()

    # Get DAG logical date
    logical_dag_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    logical_dag_date_string = logical_dag_date.strftime("%Y-%m-%d")

    # Initialize a list of the non-detail page links that have already been processed
    #links_already_processed = []

    # First, get a list of all the unique links from the Chrome webstore page
    # Excluding those on the list of links to ignore list
    # unique_links_on_edge_release_notes_page = get_unique_links_from_webpage(
    #     url=EDGE_RELEASE_NOTES,
    #     base_url=EDGE_RELEASE_NOTES,
    #     timeout_seconds=TIMEOUT_IN_SECONDS,
    #     links_to_ignore=LIST_OF_LINKS_TO_IGNORE,
    #     links_to_not_process=links_already_processed,
    # )

    # print('links found')
    # for link in unique_links_on_edge_release_notes_page:
    #     if 'march-13-2025' in link: 
    #       print(link)

    # print(' ')
    # print(' ')
    # print(' ')
    soup = get_soup_from_webpage(EDGE_RELEASE_NOTES, TIMEOUT_IN_SECONDS)

    #TEMP FOR DEVELOPMENT - write to a file
    with open("katie_edge_ouptut.html", "w", encoding="utf-8") as file:
      file.write(soup.prettify())

    #Get all h2 headers
    h2_headers = soup.find_all("h2")

    # Dictionary to store extracted text by section
    sections = {}

    for i in range(len(h2_headers)):
        
        section_title = h2_headers[i].text.strip()
        if section_title.startswith("Version "):
            next_header = h2_headers[i + 1] if i + 1 < len(h2_headers) else None

            content = []
            links = []
            for tag in h2_headers[i].find_next_siblings():
                if tag == next_header:
                    break
                if tag.name in ["p", "ul", "div"]:
                    content.append(tag.get_text(" ", strip=True))

                    #Extract links from p elements
                    link_tags_in_p = tag.find_all("a", href=True)
                    for link_tag in link_tags_in_p:
                      links.append(link_tag['href']) 
                
                if tag.name == "li":
                    link_tags_in_li = tag.find_all("a", href=True)
                    for link_tag in link_tags_in_li:
                        links.append(link_tag['href'])
                        
                    #links = [a['href'] in tag]

                #if tag.name in ["li"]:
                #    links.append(tag)
                    

            sections[section_title] = {'Content': content, 'Links': links}
            #sections[section_title]['ExtractedLinks'] = links

        ###NEXT put all links from there into its own thing



    
    print('sections')
    print(sections)

    with open("katie_sections.json", "w", encoding="utf-8") as file:
      json.dump(sections, file, indent=4, ensure_ascii=False)
            


if __name__ == "__main__":
    main()
