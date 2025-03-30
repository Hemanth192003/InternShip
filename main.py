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



# LLM Code

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from transformers import pipeline

# MongoDB connection setup
client = MongoClient("mongodb://localhost:27017/")
db = client['ResearchDB']
log_collection = db['ScrapingLogs']

# Load the summarization model
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")  # Example free model

# Function to fetch content from a URL
def fetch_content(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            # Extract main content (adjust selector based on website structure)
            paragraphs = soup.find_all("p")
            content = " ".join([para.text for para in paragraphs])
            return content
        else:
            print(f"Failed to fetch content from {url}. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred while fetching content: {e}")
        return None

# Function to summarize content based on user prompt
def summarize_content(prompt, content):
    try:
        # Combine user prompt with content
        input_text = f"{prompt}\n\n{content}"
        summary = summarizer(input_text, max_length=150, min_length=50, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        print(f"An error occurred during summarization: {e}")
        return "Unable to generate summary."

# Main workflow to fetch prompt and summarize papers from nested JSON
def process_logs_and_summarize():
    # Take the user's prompt
    user_prompt = input("Enter your prompt for summarization: ")

    # Fetch all logs from MongoDB
    logs = log_collection.find()
    for log in logs:
        sources = log.get("source", {})  # Get the nested source structure

        for source_name, papers in sources.items():
            print(f"\nProcessing papers from source: {source_name}")
            for paper in papers:
                title = paper.get("title", "No Title")
                link = paper.get("link", None)

                print(f"\nProcessing paper: {title}")
                if link:
                    content = fetch_content(link)
                    if content:
                        summary = summarize_content(user_prompt, content)
                        print(f"Summary for '{title}':\n{summary}\n")
                    else:
                        print(f"Content not available for '{title}'.")
                else:
                    print(f"No valid link for '{title}'.")

# Example Usage
if __name__ == "__main__":
    process_logs_and_summarize()