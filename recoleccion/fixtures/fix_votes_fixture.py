import json

# Load data from law_project.json
with open('law_project.json', 'r') as law_project_file:
    law_project_data = json.load(law_project_file)

# Load data from vote.json
with open('vote.json', 'r') as vote_file:
    vote_data = json.load(vote_file)

# Extract project_id values from law_project.json
law_project_ids = {item['fields']['id'] for item in law_project_data}

# Filter vote objects based on project_id values present in law_project_ids
filtered_vote_data = [
    item for item in vote_data
    if item['fields']['project_id'] in law_project_ids
]

# Save filtered data back to filtered_vote.json
with open('filtered_vote.json', 'w') as filtered_vote_file:
    json.dump(filtered_vote_data, filtered_vote_file, indent=4)

print("Filtered vote data saved to filtered_vote.json.")
