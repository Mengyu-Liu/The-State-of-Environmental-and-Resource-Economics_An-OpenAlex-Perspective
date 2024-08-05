
import requests
import pandas as pd
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# create a session
session = requests.Session()

# retries
retries = Retry(total=5, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))


# Fetch the top 1000 most cited works of each journal
# Why not fetching all works: 1. fetching top 1000 is enough for the calculation
# of top 500 mean citations for each year (each year's top 500 most cited works could
# be different), 2. too many works will fully occupy the storage and will increase
# the code running time

def get_top_cited_works(journal_id):
    base_url = "https://api.openalex.org/works"
    params = {
        "filter": f"primary_location.source.id:{journal_id}",
        "sort": "cited_by_count:desc",
        "per-page": 200,
        "cursor": "*"
    }

    results = []
    while len(results) < 1000:
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

    return results[:1000]  # Return only the first 1000 works


# Fetch citation data for the works
def get_cited_by_data(cited_by_api_url):
    params = {
        "per-page": 200,
        "cursor": "*"
    }

    cited_by_data = []
    while True:
        try:
            response = session.get(cited_by_api_url, params=params, headers={'Accept-Encoding': 'identity'})
            if response.status_code == 200:
                data = response.json()
                if 'results' in data:
                    cited_by_data.extend(data['results'])
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
            # Add delay to avoid issues caused by frequent requests
            time.sleep(1)
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            break

    return cited_by_data


# Filter works and citation data by year and calculate statistics
def filter_and_calculate(works, all_cited_by_data, year):
    filtered_works = []
    for work in works:
        publication_year = work['publication_year']
        if publication_year <= year:
            # Fetch citation data
            work_id = work['id']
            cited_by = all_cited_by_data.get(work_id, [])

            # Filter citations by year
            cited_by_count = sum(1 for citation in cited_by if citation['publication_year'] <= year)
            work['filtered_cited_by_count'] = cited_by_count
            filtered_works.append(work)

    # Sort by 'filtered_cited_by_count'
    sorted_works = sorted(filtered_works, key=lambda x: x['filtered_cited_by_count'], reverse=True)

    # Calculate the top 100 and 500 works' total and average citations
    top_100 = sorted_works[:100] if len(sorted_works) >= 100 else sorted_works
    total_cited_by_count_100 = sum(work['filtered_cited_by_count'] for work in top_100)
    average_cited_by_count_100 = total_cited_by_count_100 / len(top_100) if len(top_100) > 0 else 0

    top_500 = sorted_works[:500] if len(sorted_works) >= 500 else sorted_works
    total_cited_by_count_500 = sum(work['filtered_cited_by_count'] for work in top_500)
    average_cited_by_count_500 = total_cited_by_count_500 / len(top_500) if len(top_500) > 0 else 0

    return {
        'year': year,
        'total_100': total_cited_by_count_100,
        'average_100': average_cited_by_count_100,
        'total_500': total_cited_by_count_500,
        'average_500': average_cited_by_count_500,
        'actual_count_100': len(top_100),
        'actual_count_500': len(top_500)
    }


# Integrated Main Function
def main():
    # example
    journal_id = "S4306500963"
    # This is the example ID of Agricultural and Resource Economics: International Scientific E-Journal
    # This could be found in OpenAlex API
    print("Fetching works...")
    works = get_top_cited_works(journal_id)
    print(f"Total works: {len(works)}")

    # Fetch the citations of works of Agricultural and Resource Economics: International Scientific E-Journal
    all_cited_by_data = {}
    for work in works:
        cited_by_api_url = work.get('cited_by_api_url')
        if cited_by_api_url:
            cited_by_data = get_cited_by_data(cited_by_api_url)
            all_cited_by_data[work['id']] = cited_by_data
            print(f"Total citations for {work['id']}: {len(cited_by_data)}")

    # Define years list
    years = [2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008, 2007, 2006, 2005, 2004, 2003, 2002, 2001, 2000, 1999, 1998, 1997, 1996, 1995, 1994]

    # Combine results
    results = []
    for year in years:
        print(f"Calculating for year {year}...")
        result = filter_and_calculate(works, all_cited_by_data, year)
        results.append(result)

    # Save as Excel
    df = pd.DataFrame(results)
    output_file = 'your path'
    df.to_excel(output_file, index=False)

    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()



'''
### Merge all journals' excel files togather

import os
import pandas as pd

def collect_data_from_files(folder_path):
    all_files = [f for f in os.listdir(folder_path) if f.endswith('.xlsx')]
    data_dict = {
        'total_100': pd.DataFrame(),
        'average_100': pd.DataFrame(),
        'total_500': pd.DataFrame(),
        'average_500': pd.DataFrame(),
        'actual_count_100': pd.DataFrame(),
        'actual_count_500': pd.DataFrame(),
    }

    for file in all_files:
        file_path = os.path.join(folder_path, file)
        df = pd.read_excel(file_path)
        file_name = os.path.splitext(file)[0]  

        if 'year' not in df.columns:
            continue  

        for column in data_dict.keys():
            if column in df.columns:
                if data_dict[column].empty:
                    data_dict[column]['year'] = df['year']
                data_dict[column][file_name] = df[column]

    return data_dict

def save_combined_data(data_dict, output_file):
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        for sheet_name, data in data_dict.items():
            data.to_excel(writer, sheet_name=sheet_name, index=False)

def main():
    folder_path = 'your folder_path'
    output_file = 'your output_file'

    data_dict = collect_data_from_files(folder_path)
    save_combined_data(data_dict, output_file)
    print(f"Data combined and saved to {output_file}")

if __name__ == "__main__":
    main()
'''
