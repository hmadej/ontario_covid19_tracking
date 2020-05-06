import requests
from json import dump, load
from bs4 import BeautifulSoup
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import urlopen

PATH_TO_DATE_FILE = './datefile'
PATH_TO_JSON_DATA_FILE = './data.json'
ONTARIO_COVID19_RESOURCE_PAGE = 'https://data.ontario.ca/dataset/status-of-covid-19-cases-in-ontario/resource' \
                                '/ed270bb8-340b-41f9-a7c6-e8ef587e6d11 '
DOWNLOAD_BUTTON_TAG = 'btn btn-primary dataset-download-link resource-url-analytics resource-type-None'
TABLE_TAG = 'primary col-sm-9 col-xs-12'
TABLE_HEADER_STRING = 'Data range end'


def get_html(url):
    '''
    :param url:
    :return:
    '''
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


def get_link_to_resource_and_date():
    '''
    :return:
    '''
    data_range_end = None
    html = get_html(ONTARIO_COVID19_RESOURCE_PAGE)
    bs = BeautifulSoup(html.read(), 'html.parser')
    table = bs.find('div', {'class': TABLE_TAG})
    for tr in table.find_all("tr"):
        if tr.th.string == TABLE_HEADER_STRING:
            data_range_end = tr.td.string.strip()
            break

    download_button = bs.find('a', {'class': DOWNLOAD_BUTTON_TAG}, href=True)
    link = download_button['href']
    return data_range_end, link


def save_data_to_file(date, data):
    with open(PATH_TO_JSON_DATA_FILE, 'w') as outfile:
        dump(data, outfile)
    with open(PATH_TO_DATE_FILE, 'w') as f:
        f.write(date)


def get_date_and_data(date):
    server_date = None
    with open(PATH_TO_DATE_FILE, 'r') as f:
        date_from_file = f.read()

    if date_from_file != date:
        server_date, link = get_link_to_resource_and_date()

    if server_date and server_date == date:
        print("Requesting new data")
        if (res := requests.get(link)).status_code != 200:
            raise Exception(f"Failed to retrieve date {res.status_code}")
        else:
            result = text_to_kv_pair(res.text)
            date = server_date

    else:  # load data from file
        print("Reading data from file, no update")
        with open(PATH_TO_JSON_DATA_FILE, 'r') as infile:
            result = load(infile)
    return date, result
