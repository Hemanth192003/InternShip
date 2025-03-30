# import requests
# from bs4 import BeautifulSoup
# from pymongo import MongoClient
# from datetime import datetime
# from fuzzywuzzy import process

# # MongoDB connection setup
# client = MongoClient("mongodb://localhost:27017/")
# db = client['ResearchDB']
# log_collection = db['ScrapingLogs']

# # Function to scrape Google Scholar
# def scrape_google_scholar(topic, field):
#     base_url = "https://scholar.google.com/scholar"
#     query = f"{topic} {field}"  # Combine topic and field for search query
#     params = {"q": query, "hl": "en"}
#     response = requests.get(base_url, params=params)

#     if response.status_code == 200:
#         soup = BeautifulSoup(response.text, "html.parser")
#         results = []
#         for item in soup.select(".gs_ri"):  # Selector for research results
#             title = item.select_one(".gs_rt").text if item.select_one(".gs_rt") else "No Title"
#             link = item.select_one(".gs_rt a")['href'] if item.select_one(".gs_rt a") else "No Link"
#             author_info = item.select_one(".gs_a").text if item.select_one(".gs_a") else "No Author Info"
#             results.append({
#                 "title": title,
#                 "link": link,
#                 "author_info": author_info,
#                 "field": field  # Include field in the scraped data
#             })
#         return results
#     else:
#         print(f"Failed to fetch data from Google Scholar. Status code: {response.status_code}")
#         return []

# # Function to remove duplicates using FuzzyWuzzy
# def remove_duplicates(data):
#     unique_titles = []
#     filtered_data = []
#     for entry in data:
#         title = entry['title']
#         if not any(process.extractOne(title, unique_titles, score_cutoff=90)):
#             unique_titles.append(title)
#             filtered_data.append(entry)
#     return filtered_data

# # Function to log data into MongoDB
# def log_data(topic, field, source_site, scraped_data):
#     log_entry = {
#         "timestamp": datetime.utcnow().isoformat(),
#         "topic": topic,
#         "field": field,
#         "source_site": source_site,
#         "papers_scraped": len(scraped_data),
#         "scraped_data": scraped_data
#     }
#     log_collection.insert_one(log_entry)
#     print(f"Logged {len(scraped_data)} papers into MongoDB.")

# # Main Execution Workflow
# if __name__ == "__main__":
#     topic = "Heart Disease Prediction"  # Example topic
#     field = "Medical"  # Example field
#     source_site = "Google Scholar"

#     print(f"Scraping Google Scholar for topic: {topic} and field: {field}...")
#     google_scholar_data = scrape_google_scholar(topic, field)

#     print(f"Removing duplicates...")
#     # Uncomment the following line if you want to remove duplicates:
#     # deduplicated_data = remove_duplicates(google_scholar_data)
#     # For now, we will log the original scraped data:
#     deduplicated_data = google_scholar_data

#     print(f"Logging deduplicated data into MongoDB...")
#     log_data(topic, field, source_site, deduplicated_data)

#     print("Google Scholar scraping and logging completed successfully!")



# Connect Paper 

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
from fuzzywuzzy import process
import time

# MongoDB connection setup
client = MongoClient("mongodb://localhost:27017/")
db = client['ResearchDB']
log_collection = db['ScrapingLogs']  # Single collection for all sources

# Function to scrape Google Scholar
def scrape_google_scholar(topic, field):
    base_url = "https://scholar.google.com/scholar"
    query = f"{topic} {field}"  # Combine topic and field for search query
    params = {"q": query, "hl": "en"}
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        for item in soup.select(".gs_ri"):
            title = item.select_one(".gs_rt").text if item.select_one(".gs_rt") else "No Title"
            link = item.select_one(".gs_rt a")['href'] if item.select_one(".gs_rt a") else "No Link"
            author_info = item.select_one(".gs_a").text if item.select_one(".gs_a") else "No Author Info"
            results.append({
                "title": title,
                "link": link,
                "author_info": author_info,
                "field": field,  # Include field in the scraped data
                "source": "Google Scholar"  # Add source for segregation
            })
        return results
    else:
        print(f"Failed to fetch data from Google Scholar. Status code: {response.status_code}")
        return []

# Function to scrape ResearchGate
def scrape_researchgate(topic):
    base_url = f"https://www.researchgate.net/search/publication?q={topic.replace(' ', '%20')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    session = requests.Session()
    session.headers.update(headers)

    try:
        response = session.get(base_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            results = []
            for result in soup.select(".nova-o-stack__item"):
                title = result.select_one(".nova-e-text--spacing-none").text.strip() if result.select_one(".nova-e-text--spacing-none") else "No Title"
                link = result.select_one("a")['href'] if result.select_one("a") else "No Link"
                link = f"https://www.researchgate.net{link}" if "http" not in link else link
                results.append({
                    "title": title,
                    "link": link,
                    "author_info": "Not Available",  # ResearchGate doesn't offer author info directly
                    "field": "Not Specified",
                    "source": "ResearchGate"  # Add source for segregation
                })
            return results
        else:
            print(f"Failed to fetch data from ResearchGate. Status code: {response.status_code}")
            return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

# Function to remove duplicates using FuzzyWuzzy
def remove_duplicates(data):
    # unique_titles = []
    # filtered_data = []
    # for entry in data:
    #     title = entry['title']
    #     if not any(process.extractOne(title, unique_titles, score_cutoff=90)):
    #         unique_titles.append(title)
    #         filtered_data.append(entry)
    return data

# Function to log data into MongoDB with nested structure
def log_nested_data(scraped_data):
    # Create a dictionary to organize data by source
    sources = {}

    for entry in scraped_data:
        source = entry.get('source', "Unknown")
        if source not in sources:
            sources[source] = []  # Initialize source as a list of entries
        sources[source].append({
            "timestamp": datetime.utcnow().isoformat(),
            "title": entry['title'],  # Scraped title
            "link": entry['link'],  # Scraped link
            "author_info": entry.get('author_info', "Not Available"),  # Authors
            "field": entry.get('field', "Not Specified")  # Research field
        })

    # Create the final JSON document with nested "source" field
    final_log = {
        "source": sources  # Nested source-based structure
    }

    # Insert the final log into MongoDB
    log_collection.insert_one(final_log)
    print("Logged nested data structure into MongoDB!")

# Main Execution Workflow
if __name__ == "__main__":
    topic = "Heart Disease Prediction"  # Example topic
    field = "Medical"  # Example field

    all_scraped_data = []

    # Scrape Google Scholar
    print(f"Scraping Google Scholar for topic: {topic} and field: {field}...")
    google_scholar_data = scrape_google_scholar(topic, field)
    if google_scholar_data:
        print(f"Removing duplicates from Google Scholar data...")
        google_scholar_deduped = remove_duplicates(google_scholar_data)
        all_scraped_data.extend(google_scholar_deduped)

    # Scrape ResearchGate
    print(f"Scraping ResearchGate for topic: {topic}...")
    researchgate_data = scrape_researchgate(topic)
    if researchgate_data:
        print(f"Removing duplicates from ResearchGate data...")
        researchgate_deduped = remove_duplicates(researchgate_data)
        all_scraped_data.extend(researchgate_deduped)

    # Log data into MongoDB with nested structure
    print(f"Logging data into MongoDB with nested source structure...")
    log_nested_data(all_scraped_data)

    print("Scraping and logging process completed successfully!")