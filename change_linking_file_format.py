import json

ORIGINAL_FILE = "recoleccion/components/linkers/training/tests/PersonLinker.json"
MODIFIED_FILE = "recoleccion/components/linkers/training/tests/PersonLinker_modified.json"


# Load the JSON data
with open(ORIGINAL_FILE, "r", encoding="utf-8-sig") as file:
    data = json.load(file)

# Process the "distinct" records
for record in data["distinct"]:
    name = record["__value__"][0]["name"]
    last_name = record["__value__"][0]["last_name"]
    full_name = last_name + " " + name
    record["__value__"][0] = {"full_name": full_name}

    name = record["__value__"][1]["name"]
    last_name = record["__value__"][1]["last_name"]
    full_name = last_name + " " + name
    record["__value__"][1] = {"full_name": full_name}

# Process the "match" records
for record in data["match"]:
    name = record["__value__"][0]["name"]
    last_name = record["__value__"][0]["last_name"]
    full_name = last_name + " " + name
    record["__value__"][0] = {"full_name": full_name}

    name = record["__value__"][1]["name"]
    last_name = record["__value__"][1]["last_name"]
    full_name = last_name + " " + name
    record["__value__"][1] = {"full_name": full_name}

# Save the modified data
with open(MODIFIED_FILE, "w", encoding="utf-8-sig") as file:
    json.dump(data, file, indent=4)
