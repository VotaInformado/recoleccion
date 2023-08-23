import json
import sys

# Cuando se importan fixtures directo de la base de dato, no vienen en el formato que necesita Django para las pruebas
# La idea de este script es que se le pase como argumento el nombre del archivo de la fixture y lo arregle


def fix_file(class_name):
    file_name = f"{class_name}.json"
    with open(file_name, "r") as file:
        data = json.load(file)

        # Iterate through the list of dictionaries and add "model" key
        for item in data:
            item["model"] = f"recoleccion.{class_name}"

        # Save the modified data back to the JSON file
        with open(file_name, "w") as file:
            json.dump(data, file, indent=4)


def fix_fields(class_name):
    file_name = f"{class_name}.json"
    with open(file_name, "r") as file:
        data = json.load(file)

    # Create a new list to store the modified dictionaries
    new_data = []

    # Iterate through the list of dictionaries and restructure them
    for item in data:
        # Create a new dictionary with "fields" key
        new_item = {"fields": {}}

        # Copy the existing key-value pairs to the "fields" dictionary
        for key, value in item.items():
            if key != "model":
                new_item["fields"][key] = value
            else:
                new_item[key] = value

        # Append the modified dictionary to the new_data list
        new_data.append(new_item)

    # Save the modified data back to the JSON file
    with open(file_name, "w") as file:
        json.dump(new_data, file, indent=4)

file_name = sys.argv[1]
fix_file(file_name)
fix_fields(file_name)
