# script for fetching loc data for lab 5
import requests as req
import json
from pathlib import Path
import os

LOC_ROOT = "https://loc.gov/"
LCCN_ROOT = 'https://lccn.loc.gov/'
SEARCH_ROOT = 'https://www.loc.gov/search'


def fetch_urls(url: str, params: dict = None, root: str = None) -> req.Response:
    """
    Fetches a web page from a URL.

    Args:
        url (str): The URL to fetch. If root is provided, it will be treated as an endpoint to the root.
        params (dict, optional): A dictionary of query string parameters to send with the request. Defaults to None.
        root (str, optional): A root URL to prepend to the URL. Defaults to None.

    Raises:
        Exception: If there is an error fetching the URL or parsing the title, it will be caught and printed.

    Returns:
        req.Response: The HTTP response object.
    """
    if root:
        url = root + url if url[0] != "/" else root + url[1:]
    try:
        resp = req.get(url=url, params=params)
        if params and 'fo' in params.keys():
            try:
                print(f'LCCN number and permalink: {resp.json()["item"]["library_of_congress_control_number"]}, {LCCN_ROOT}{resp.json()["item"]["library_of_congress_control_number"]}')
            except KeyError:
                print("*Informational* Tried to print LCCN number and permalink but failed")
                pass
        return resp
    except Exception as e:
        print(f"Error for {url}: {e}")


def save_to_file(res: req.Response, filename: str):
    """
    Saves the content of an HTTP response to a file.

    If the response content type is JSON, the content is saved as a JSON file.
    Otherwise, the content is saved as a text file.

    Args:
        res (req.Response): The HTTP response object containing the content to save.
        filename (str): The base name of the file to save the content to (without extension).

    Raises:
        Exception: If there is an error during the file writing process.

    Returns:
        None.
    """
    try:
        if 'json' in res.headers.get('content-type').lower():
            with open(f'{filename}.json', "w", encoding='utf-8') as f:
                json.dump(res.json(), f, ensure_ascii=False, indent=2)
            print(f"File has been written to {Path.cwd()} as {filename}.json")
        else:
            with open(f'{filename}.txt', 'w', encoding='utf-8') as f:
                f.write(res.text)
    except Exception as e:
        print(f'Error saving file: {e}')


def get_params() -> dict:
    """
    Prompts the user for a search query and a format preference, then returns these parameters as a dictionary.

    Args:
        None.

    Returns:
        dict: A dictionary containing the search query and format preference, or None if no parameters were provided.
            - 'q' (str): The search query input by the user.
            - 'fo' (str): The format preference ('json') if the user requested JSON format.
    """
    p = {}
    query = input("Input a search query here, or hit enter to skip: ")
    json = input("Would you like to request JSON format? y/n: ").strip().lower()
    if query:
        p['q'] = query
    if json == 'y':
        p['fo'] = 'json'
    return p if p else None


def main():
    endpoints = [
        "resource/cph.3f05183",
        "resource/fsa.8d24709",
        "resource/highsm.64003",
        "resource/ds.06560/",
        "resource/ppmsca.18016/",
        "resource/hhh.ok0012.sheet/?sp=8&q=hhh.ok0012",
        "resource/cph.3f05183/",
        "resource/highsm.20336/",
        "Custom endpoint",
    ]
    params = get_params()
    if params and 'q' in params.keys():
        # if a search query is present, uses the SEARCH_ROOT
        fetch_res = fetch_urls(SEARCH_ROOT, params=params)
        save = input("Would you like to save the output to a file? y/n: ").strip().lower()
        if save == 'y':
            fn = input("Enter a filename for the file (no extensions): ").strip()
            save_to_file(fetch_res, fn)
        return

    print("Choose the corresponding number of one of the default endpoints below: ")
    print(f"{os.linesep.join(f'{h}. {i}'for h, i in enumerate(endpoints, start=1))}\n")
    ep = input("Your choice: ")
    while True:
        try:
            ep = int(ep) - 1
            endpoints[ep]
            break
        except:
            ep = input("Invalid choice, try again: ")
    if endpoints[ep] == endpoints[-1]:
        endpoints[-1] = input("Enter your custom endpoint: ").strip()
    fetch_res = fetch_urls(endpoints[ep], params=params, root=LOC_ROOT)
    save = input("Would you like to save the output to a file? y/n: ").strip().lower()
    if save == 'y':
            fn = input("Enter a filename for the file (no extensions): ").strip()
            save_to_file(fetch_res, fn)
    return

if __name__ == "__main__":
    main()

# a. resource/cph.3f05183 LCCN number and permalink: 98508155, https://lccn.loc.gov/98508155

# b. resource/fsa.8d24709  LCCN number and permalink: 2017843202, https://lccn.loc.gov/2017843202

# c. resource/highsm.64003 LCCN number and permalink: 2020722343, https://lccn.loc.gov/2020722343
