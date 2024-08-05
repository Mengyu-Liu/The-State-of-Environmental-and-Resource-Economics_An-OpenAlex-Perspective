
import requests
import pandas as pd
import os
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Create a session
session = requests.Session()

# Set retries
retries = Retry(total=5, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))

# Fetch the top 800 most cited works of each journal
# Why not fetching all works: fetching top 800 is enough for the identification
# of top 20 most cited papers in general economics journals

def get_top_cited_works(journal_id):
    base_url = "https://api.openalex.org/works"
    params = {
        "filter": f"primary_location.source.id:{journal_id}",
        "sort": "cited_by_count:desc",
        "per-page": 200,
        "cursor": "*"
    }

    results = []
    while len(results) < 800:
        try:
            response = session.get(base_url, params=params, headers={'Accept-Encoding': 'identity'})
            if response.status_code == 200:
                data = response.json()
                if 'results' in data:
                    results.extend(data['results'])
                next_cursor = data.get('meta', {}).get('next_cursor')
                print(f"Next cursor: {next_cursor}")  # Print cursor value for debugging
                if next_cursor:
                    params['cursor'] = next_cursor  # Update cursor for the next page
                else:
                    break  # End loop when no more data is available
            else:
                print(f"Failed to fetch data: {response.status_code}")
                print("Error response:", response.text)  # Print detailed error information
                break
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            break

        # Add delay to avoid issues caused by frequent requests
        time.sleep(1)

    return results[:800]  # Return only the first 800 works

# filter works by designated terms in API fields of 'title', 'concepts', 'keywords'. 'topics'
def filter_works_by_keywords(works, keywords):
    filtered_works = []
    for work in works:
        title = work.get('title', '')
        concepts = [concept['display_name'] for concept in work.get('concepts', []) if isinstance(concept['display_name'], str)]
        keywords_list = [kw for kw in work.get('keywords', []) if isinstance(kw, str)]
        topics = [topic['display_name'] for topic in work.get('topics', []) if isinstance(topic['display_name'], str)]

        combined_list = concepts + keywords_list + topics + [title]

        for keyword in keywords:
            for item in combined_list:
                if keyword.lower() in item.lower():
                    filtered_works.append(work)
                    break  # Break out of the inner loop as soon as one keyword is matched
            else:
                continue
            break  # Break out of the outer loop as soon as one keyword is matched

    return filtered_works

# Integrated Main Function
def main():
    # example
    # journal ID could be found in OpenAlex API
    journal_id = "S199447588"  # ID
    print("Fetching top cited works...")
    works = get_top_cited_works(journal_id)
    print(f"Total works fetched: {len(works)}")

    # Define designated keywords terms list
    keywords = ["Environment", "Environmental", "Pollution", "Energy", "Climate", "Carbon", "Resource", "Resources"]

    # Filter works with designated keywords terms
    filtered_works = filter_works_by_keywords(works, keywords)
    print(f"Total filtered works: {len(filtered_works)}")

    # save filtered works as an Excel file
    df = pd.DataFrame(filtered_works)
    output_folder = 'your file path'
    os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(output_folder, 'the_file_name')
    df.to_excel(output_file, index=False)

    print(f"Filtered works saved to {output_file}")

if __name__ == "__main__":
    main()


'''
import pandas as pd
import os

# Rank all works from the 12 general economics journals filtered above
input_folder = 'your folder path'
output_file = os.path.join(input_folder, 'combined_papers_general_economics.xlsx')

# Fetch all Excel files in your folder path
excel_files = [f for f in os.listdir(input_folder) if f.endswith('.xlsx')]


combined_df = pd.DataFrame()


for file in excel_files:
    file_path = os.path.join(input_folder, file)


    df = pd.read_excel(file_path)


    source_name = file.split('_')[0]
    df['source_name'] = source_name


    df = df.sort_values(by='cited_by_count', ascending=False)


    combined_df = pd.concat([combined_df, df])


combined_df.to_excel(output_file, index=False)

print(f"Combined data saved to {output_file}")
'''
