import requests
from json import dump, load, loads
from bs4 import BeautifulSoup
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import urlopen

PATH_TO_JSON_DATE_FILE = "./datefilejson"
PATH_TO_GEOJSON_DATE_FILE = "./datefilegeojson"
PATH_TO_JSON_DATA_FILE = "./data.json"
PATH_TO_GEOJSON_DATA_FILE = "./conposcovidloc.geojson"
LAST_VALIDATED_DATE = "Last Validated Date"
TAG_RESOURCE = 'resource-url-analytics btn btn-primary dataset-download-link'
BASE_URL = "https://data.ontario.ca/"
ONTARIO_COVID19_GEOJSON = ".geojson"
ONTARIO_COVID19_CSV = ".csv"
ONTARIO_COVID19_POS_LINK = "dataset/confirmed-positive-cases-of-covid-19-in-ontario"
ONTARIO_COVID19_STATUS_LINK = "dataset/status-of-covid-19-cases-in-ontario"


def get_html(url):
    html = None
    try:
        html = urlopen(url)
    except HTTPError as e:
        print(e)
    except URLError as u:
        print(u)
    finally:
        return html


def text_to_kv_pair(text):
    csv_key_pair = dict()
    row_strings = text.split('\n')

    def clean(list_of_strings):
        return [x.strip('\r') for x in list_of_strings]

    rows = [clean(a) for a in [x.split(',') for x in row_strings]]

    def string_to_int(int_string):
        return 0 if int_string == '' else int(int_string)

    headers, data = rows[0], rows[1:-1]
    for row in data:
        date = row[0]
        csv_key_pair[date] = dict(zip(headers[1:], list(map(string_to_int, row[1:]))))
    return csv_key_pair


def save_data_to_file(date, data, filetype):
    if filetype == ONTARIO_COVID19_CSV:
        path_to_file = PATH_TO_JSON_DATA_FILE
        path_to_date_file = PATH_TO_JSON_DATE_FILE
    else:
        path_to_file = PATH_TO_GEOJSON_DATA_FILE
        path_to_date_file = PATH_TO_GEOJSON_DATE_FILE

    with open(path_to_file, 'w') as outfile:
        dump(data, outfile)
    with open(path_to_date_file, 'w') as f:
        f.write(date)


def get_date_and_data(date, link, filetype):
    server_date = None
    if filetype == ONTARIO_COVID19_CSV:
        path_to_date_file = PATH_TO_JSON_DATE_FILE
    else:
        path_to_date_file = PATH_TO_GEOJSON_DATE_FILE

    with open(path_to_date_file, 'r') as f:
        date_from_file = f.read()

    if date_from_file != date:
        server_date, link = get_resource(link, filetype)

    if server_date and server_date == date:
        print("Requesting new data")
        if (res := requests.get(link)).status_code != 200:
            raise Exception(f"Failed to retrieve date {res.status_code}")
        else:
            if filetype == ONTARIO_COVID19_CSV:
                result = text_to_kv_pair(res.text)
            else:
                result = loads(res.text)
            date = server_date

    else:  # load data from file
        print("Reading data from file, no update")
        if filetype == ONTARIO_COVID19_CSV:
            path_to_file = PATH_TO_JSON_DATA_FILE
        else:
            path_to_file = PATH_TO_GEOJSON_DATA_FILE
        with open(path_to_file, 'r') as infile:
            result = load(infile)

    return date, result


def get_resource(resource_path, filetype):
    date = None
    html = get_html(BASE_URL + resource_path)
    bs = BeautifulSoup(html.read(), 'html.parser')
    section = bs.find('section', {"class": "additional-info"})
    table = section.find('table')
    for tr in table.find_all("tr"):
        if tr.th.string == LAST_VALIDATED_DATE:
            date = tr.td.string.strip()
            break

    download_buttons = bs.find_all('a', {'class': TAG_RESOURCE}, href=True)
    for button in download_buttons:
        if filetype in button['href']:
            download_link = button['href']
            break
    return date, download_link
