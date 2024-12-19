# tool for creating a csv file from LoC metadata for ingestion into Omeka S
# via the CSV Import module.
# compliments, and is complimented by, collection-extract-tools.py.
# desgined in accordance with the Metadata Application Profile for the Library of
# Congress Free-to-Use: Libraries set.

from datetime import date, datetime
import re
import html
import csv
import json
from pathlib import Path

METADATA = (Path(__file__).parent / Path("item-metadata")).resolve()

if not METADATA.exists():
    raise FileNotFoundError(f"Metadata path does not exist: {METADATA}")


def extract_dates(text: str) -> list:
    """
    Extracts dates from text.
    Supported formats:
    - Single year (e.g., "1999")
    - Year range (e.g., "1999-2001")
    - Year and month (e.g., "1941 Sept.")
    - Month and year (e.g., "September 2012")
    - Full ISO date (e.g., "2015-09-30")
    Args:
        text (str): Input text.
    Returns:
        list: Extracted dates in "YYYY", "YYYY/YYYY", "YYYY-MM", or "YYYY-MM-DD" format.
    """

    results = []

    # patterns to match various date formats
    patterns = [
        r"\b(?:c|ca\.?|between|after|before|in|on|around|circa)?\s*\[?\s*(\d{4})\s*\]?\b",  # single year
        r"\b(?:c|ca\.?|between|after|before|in|on|around|circa)?\s*\[?\s*(\d{4})\s*(?:and|-|to|/|or)\s*(\d{4})\s*\]?\b",  # year range
        r"\b(\d{4})\s*([A-Za-z]+)\b",  # year and month (like "1941 sept.")
        r"\b([A-Za-z]+)\s+(\d{4})\b",  # month and year (like "september 2012")
        r"\b(\d{4})-(\d{2})-(\d{2})\b",  # full iso date (like "2015-09-30")
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if len(match) == 1:  # single year
                year = match[0]
                results.append(year)
            elif len(match) == 2:  # month-year or year-month
                if match[0].isdigit():  # e.g., "1941 sept."
                    year, month = match
                else:  # e.g., "september 2012"
                    month, year = match
                try:
                    # parse and reformat month-year to iso (yyyy-mm)
                    month_number = datetime.strptime(
                        month[:3], "%b"
                    ).month  # handle abbreviations like "sept"
                    formatted_date = f"{year}-{month_number:02d}"
                    results.append(formatted_date)
                except ValueError:
                    continue
            elif len(match) == 3:  # full iso date (like 2015-09-30) or year-range
                if match[0].isdigit() and match[1].isdigit() and match[2].isdigit():
                    # full date in iso (yyyy-mm-dd)
                    year, month, day = match
                    formatted_date = f"{year}-{month}-{day}"
                    results.append(formatted_date)
                else:
                    # year range (like "1900 and 1905")
                    start_year, end_year = match[0], match[2]
                    results.append(f"{start_year}/{end_year}")
            else:
                continue

    return results


def determine_extent_form(container: list) -> str | tuple:
    """
    Determines the physical extent and physical form from a container list.

    Args:
        container (list): List of extent and form descriptions.

    Returns:
        str | tuple:
            - Tuple with joined items and "N/A" if container has multiple items.
            - Tuple with extent and form extracted using regex if single item has both colon and semicolon.
            - Tuple with extent and form split by colon if single item has a colon.
            - Tuple with single item and "N/A" otherwise.

    Note:
        Does not handle cases where Physical Form is conjoined with Physical Extent.
    """

    # I'd like to note here a single item this function doesn't account for,
    # resulting in an instance of the Physical Form being conjoined
    # with the Physical Extent. this could be resolved, but in lieu of
    # any other instances of this issue arising, I chose to leave it be
    if len(container) > 1:
        return (";".join(container), "N/A")

    if ":" in container[0] and ";" in container[0]:
        # regex pattern to extract text before colon, between colon and
        # semicolon, and after semicolon
        match = re.match(r"^(.*?)\s*:\s*(.*?)\s*;\s*(.*)$", container[0])
        extent1, form, extent2 = match.group(1), match.group(2), match.group(3)
        return (";".join([extent1, extent2]), form)
    elif ":" in container[0]:
        extent, form = container.split(" : ")
        return (extent, form)
    else:
        return (container[0], "N/A")


def clean_html_text(html_text: str) -> str:
    """
    Cleans the provided HTML text by performing the following steps:
    1. Removes HTML tags.
    2. Decodes HTML escape sequences (e.g., &nbsp;) to their corresponding characters.
    3. Replaces multiple spaces, tabs, and newlines with a single space.
    Args:
        html_text (str): The HTML text to be cleaned.
    Returns:
        str: The cleaned text with HTML tags removed, escape sequences decoded,
             and extraneous whitespace characters replaced by a single space.
    """

    # remove HTML tags
    no_tags = re.sub(r"<[^>]+>", " ", html_text)

    # decode HTML escape sequences (&nbsp; etc) to a space
    decoded_text = html.unescape(no_tags)

    # Step 3: Replace multiple spaces, tabs, and newlines with a single space
    cleaned_text = re.sub(r"\s+", " ", decoded_text).strip()

    return cleaned_text


def main() -> None:
    data_list = []
    td = date.today().strftime("%Y-%m-%d")
    file_open_error = 0
    dc = "dcterms:"
    mods = "mods:"

    for i in METADATA.iterdir():
        try:
            with open(i, "r", encoding="utf-8") as f:
                data = json.load(f).get("item", {})
                deep_data = data.get("item", {})
                data_dict = {}
                if data:
                    data_dict["item_type"] = "Item"
                    data_dict["date_uploaded"] = td
                    data_dict["source_file"] = str(i)
                    data_dict[f"{dc}title"] = data.get("title", "N/A")
                    data_dict[f"{dc}created"] = extract_dates(
                        data.get("created_published_date", "N/A")
                    )
                    # dynamically decides if description will be sourced from the 'description' attribute
                    # or the item['notes'] attribute.
                    # searches for the specified pattern ('. | ') and pulls
                    # the text that would apear after said pattern. If this
                    # is not sucecssful, falls back to joining the item['notes]
                    # attribute into a single string, which is the 'x' argument
                    # passed to the lambda function
                    data_dict[f"{dc}description"] = lambda x: (
                        re.search(
                            r"\. \| (.+)", data.get("description", ["N/A"])[0]
                        ).group(1)
                        if re.search(r"\. \| (.+)", data.get("description", ["N/A"])[0])
                        else " ".join(x)
                    )(deep_data.get("notes", ["N/A"]))
                    data_dict[f"{dc}contributor"] = ";".join(
                        data.get("contributor_names", ["N/A"])
                    )
                    data_dict[f"{dc}identifier:controlNumber"] = deep_data.get(
                        "control_number"
                    )
                    data_dict[f"{mods}locationUrl"] = data.get("link", "N/A")
                    data_dict[f"{mods}mediaType"] = data.get("mime_type", "N/A")
                    ext_form = determine_extent_form(data.get("medium"))
                    data_dict[f"{mods}physicalExtent"] = ext_form[0]
                    data_dict[f"{mods}physicalForm"] = ext_form[1]
                    data_dict[f"{dc}subject"] = ";".join(
                        data.get("subject_headings", ["N/A"])
                    )
                    data_dict[f"{dc}language"] = data.get("language", ["N/A"])[0]
                    # populates Access Condition based on either availability
                    # of the attributes specified below
                    data_dict[f"{mods}accessCondition"] = (
                        data.get("rights_advisory")
                        if data.get("rights_advisory")
                        else data.get("rights_information")
                    )
                    data_dict[f"{dc}rights"] = clean_html_text(
                        data.get("rights", "N/A")
                    )
                else:
                    print(f"No data from {str(i)}:(")
                data_list.append(data_dict)
        except Exception as e:
            print(f"Error opening {i}: {e}")
            file_open_error += 1

    try:
        with open("omeka-ingest-data.csv", "w", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data_list[0].keys())
            writer.writeheader()
            for row in data_list:
                writer.writerow(row)
        print(
            f"File has been written to {Path(__file__).parent} as {'omeka-ingest-data.csv'}"
        )
        return
    except Exception as e:
        print(f"Error saving file: {e}")


if __name__ == "__main__":
    main()
