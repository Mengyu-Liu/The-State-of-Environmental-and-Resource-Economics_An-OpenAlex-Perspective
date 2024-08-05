
import pandas as pd
import requests

journal_id = "S2764690092"
# The example journal id of Economics and Policy of Energy and the Environment
# This could be found in each journal's OpenAlex API
base_url = "https://api.openalex.org/works"
params = {
    "filter": f"locations.source.id:{journal_id}",
    "per-page": 200,
    "cursor": "*"  # Initial cursor
}

results = []
while True:
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        results.extend(data['results'])
        next_cursor = data.get('meta', {}).get('next_cursor')
        print(f"Next cursor: {next_cursor}")  # Print cursor value for debugging
        if next_cursor:
            params['cursor'] = next_cursor  # update cursor for the next page
        else:
            break  # End loop when no more data is available
    else:
        print(f"Failed to fetch data: {response.status_code}")
        print("Error response:", response.text)  # Print detailed error information
        break

print(f"Total results: {len(results)}")

# Print the first 10 records for validation
for i, result in enumerate(results[:10], 1):
    print(f"{i}: {result}")

# Rank papers by citation count and export to Excel
sorted_papers = sorted(results, key=lambda x: x['cited_by_count'], reverse=True)
df = pd.DataFrame(sorted_papers)
excel_file_path = 'your excel path'
df.to_excel(excel_file_path, index=False)
print("Excel export is finished")

# calculate the total citations and average citations
# of the top 500 most cited papers in each journal
top_500_papers = sorted_papers[:500] if len(sorted_papers) >= 500 else sorted_papers
total_cited_by_count_500 = sum(paper['cited_by_count'] for paper in top_500_papers)
average_cited_by_count_500 = total_cited_by_count_500 / len(top_500_papers)

# print the results of top 500 total and mean citations
print("Top 500 cited_by_count_total：", total_cited_by_count_500)
print("Top 500 cited_by_count_average：", average_cited_by_count_500)

# calculate the total citations and average citations
# of the top 1000 most cited papers in each journal
top_1000_papers = sorted_papers[:1000] if len(sorted_papers) >= 1000 else sorted_papers
total_cited_by_count_1000 = sum(paper['cited_by_count'] for paper in top_1000_papers)
average_cited_by_count_1000 = total_cited_by_count_1000 / len(top_1000_papers)

# print the results of top 1000 total and mean citations
print("Top 1000 cited_by_count_total：", total_cited_by_count_1000)
print("Top 1000 cited_by_count_average：", average_cited_by_count_1000)
