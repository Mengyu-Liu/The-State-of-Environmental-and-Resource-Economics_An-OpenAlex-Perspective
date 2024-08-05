#'''
import requests
import pandas as pd
from collections import defaultdict
import os
import time

# Set the designated terms lists
stated_preference_keywords = [
    "stated preference", "stated preference methods",
    "discrete choice models", "conjoint analysis", "contingent valuation", "willingness to pay"
]
revealed_preference_keywords = [
    "revealed preference", "revealed preference methods", "hedonic pricing",
    "hedonic index", "property values", "house prices"
]

# Journal id can be found in OpenAlex API
journal_id = "https://openalex.org/S4210216073"

# Define API headers
headers = {
    "Accept": "application/json"
}

# Fetch all works of the journal
def get_works(journal_id):
    base_url = "https://api.openalex.org/works"
    params = {
        "filter": f"primary_location.source.id:{journal_id}",
        "per-page": 200,
        "cursor": "*"
    }

    results = []
    while True:
        try:
            response = requests.get(base_url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if 'results' in data:
                    results.extend(data['results'])
                else:
                    print("No 'results' key found in the response.")
                    print("Response data:", data)  # print response data for debugging
                    break
                next_cursor = data.get('meta', {}).get('next_cursor')
                print(f"Next cursor: {next_cursor}")  # print cursor for debugging
                if next_cursor:
                    params['cursor'] = next_cursor  # Update the cursor to fetch the next page
                else:
                    break  # End the loop when no more data is available
            else:
                print(f"Failed to fetch data: {response.status_code}")
                print("Error response:", response.text)  # Print detailed error information
                break
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            break

        # Add a delay to avoid issues caused by frequent requests
        time.sleep(1)

    return results

# Count the frequency of the designated terms in 'keywords' and 'concepts' API fields
def count_keywords(work, keywords):
    count = 0
    keywords_list = work.get('keywords', [])
    concepts = work.get('concepts', [])

    for keyword in keywords:
        for kw in keywords_list:
            if keyword.lower() in kw['display_name'].lower():
                count += 1
        for concept in concepts:
            if keyword.lower() in concept['display_name'].lower():
                count += 1
    return count

# Main function
# Compare the counts of designated SP and RP terms.
# For a publication, if the count of designated SP terms exceeds that of RP terms,
# it is classified as an SP work, and vice versa.
def main():
    works = get_works(journal_id)
    keyword_counts = []
    yearly_stats = defaultdict(lambda: {'stated_preference_higher': 0, 'revealed_preference_higher': 0})

    for work in works:
        year = work['publication_year']
        stated_preference_count = count_keywords(work, stated_preference_keywords)
        revealed_preference_count = count_keywords(work, revealed_preference_keywords)

        keyword_counts.append({
            'id': work['id'],
            'title': work['title'],
            'year': year,
            'stated_preference_count': stated_preference_count,
            'revealed_preference_count': revealed_preference_count
        })

        if stated_preference_count > revealed_preference_count:
            yearly_stats[year]['stated_preference_higher'] += 1
        elif revealed_preference_count > stated_preference_count:
            yearly_stats[year]['revealed_preference_higher'] += 1

    # Convert the frequency results of designated terms for each work into a DataFrame and save it as an Excel file
    df_work_keywords = pd.DataFrame(keyword_counts)
    output_path_work_keywords = r"your_output_path_with_excel_file_name"
    os.makedirs(os.path.dirname(output_path_work_keywords), exist_ok=True)
    df_work_keywords.to_excel(output_path_work_keywords, index=False)
    print(f"the results of all works are saved as {output_path_work_keywords}")

    # Convert the frequency results of designated terms for each year into a DataFrame and save it as an Excel file
    df_yearly_stats = pd.DataFrame(yearly_stats).T.sort_index()
    output_path_yearly_stats = r"your_another_output_path_with_excel_file_name"
    df_yearly_stats.to_excel(output_path_yearly_stats)
    print(f"the annual combined results are saved as {output_path_yearly_stats}")

if __name__ == "__main__":
    main()
#'''


#'''
import pandas as pd
import os

# The below codes are utilized to combine the results of all journals
# Define directory path
directory_path = r"your_directory_path"

# Initialize an empty DataFrame to store the aggregated data
summary_df = pd.DataFrame()

# Iterate through all files in the directory
for filename in os.listdir(directory_path):
    if "_total_keywords" in filename and filename.endswith(".xlsx"):
        file_path = os.path.join(directory_path, filename)
        df = pd.read_excel(file_path)

        # Check if the DataFrame is empty
        if df.empty:
            print(f" {filename} is empty，skip the file")
            continue

        # Ensure column names are consistent
        df.columns = ['year', 'stated_preference_higher', 'revealed_preference_higher']

        # If 'summary_df' is empty, assign the value directly
        if summary_df.empty:
            summary_df = df
        else:
            # Aggregate the data by year
            summary_df = pd.merge(summary_df, df, on='year', how='outer', suffixes=('', '_dup'))

            # Combine the data in the columns
            summary_df['stated_preference_higher'] = summary_df[
                ['stated_preference_higher', 'stated_preference_higher_dup']].sum(axis=1, skipna=True)
            summary_df['revealed_preference_higher'] = summary_df[
                ['revealed_preference_higher', 'revealed_preference_higher_dup']].sum(axis=1, skipna=True)

            # Remove unnecessary duplicate columns
            summary_df.drop(columns=['stated_preference_higher_dup', 'revealed_preference_higher_dup'], inplace=True)

# Check if 'summary_df' is empty
if summary_df.empty:
    print("No valid _total_keywords files found or all files are empty")
else:
    # Save results as new Excel file
    output_path = os.path.join(directory_path, "SP vs RP.xlsx")
    summary_df.to_excel(output_path, index=False)
    print(f"The aggregated results have been saved to {output_path}")
#'''
