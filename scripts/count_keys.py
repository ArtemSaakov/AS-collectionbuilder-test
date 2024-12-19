# a little tool to count inspect and compare keys

from pathlib import Path
import json

directory = Path.cwd() / Path('collection-data/item-metadata')  # Replace with your directory
key_to_check = 'medium'  # Replace with the key you want to check
key_to_compare = 'medium'  # Replace with the key you want to compare

custom_key_count = 0
count = 0

for filepath in directory.glob('*.json'):
    with open(filepath, 'r') as file:
        try:
            data = json.load(file)
            data = data.get('item', data)
            count += 1
            key1 = data['item'].get(key_to_check, None)
            key2 = data.get(key_to_compare, None)
            with open('output.txt', 'a') as f:
                f.write(f'{filepath.name}:\nlanguage: {key1}\nlanguage #2: {key2}\n')

        except json.JSONDecodeError:
            print(f"Error decoding JSON in file {filepath.name}")

print(f"Number of files where '{key_to_check}' is the same as {key_to_compare}: {custom_key_count}")
print(f"Total number of files checked: {count}")

