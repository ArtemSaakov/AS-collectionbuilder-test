# a little tool to count inspect and compare keys

from pathlib import Path
import json

directory = Path.cwd() / Path('collection-data/item-metadata')  # Replace with your directory
key_to_check = 'date'  # Replace with the key you want to check
key_to_compare = 'rights_information'  # Replace with the key you want to compare

empty_key_count = 0
count = 0

for filepath in directory.glob('*.json'):
    with open(filepath, 'r') as file:
        try:
            data = json.load(file)
            data = data.get('item', data)
            count += 1
            key1 = data.get(key_to_check, None)
            key2 = data.get(key_to_compare, None)
            print(key1, key2)
            if key1:
                empty_key_count += 1
            else:
                print(f"File {filepath.name} does not have '{key_to_check}' equal to '{key_to_compare}'")
        except json.JSONDecodeError:
            print(f"Error decoding JSON in file {filepath.name}")

print(f"Number of files where '{key_to_check}' is empty: {empty_key_count}")
print(f"Total number of files checked: {count}")