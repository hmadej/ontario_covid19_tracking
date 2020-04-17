import requests
import json
import math
import datetime
import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline
import numpy as np
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import urlopen
from bs4 import BeautifulSoup

ONTARIO_COVID19_RESOURCE_PAGE = 'https://data.ontario.ca/dataset/status-of-covid-19-cases-in-ontario/resource/ed270bb8' \
                                '-340b-41f9-a7c6-e8ef587e6d11 '
DOWNLOAD_BUTTON_TAG = 'btn btn-primary dataset-download-link resource-url-analytics resource-type-None'
TABLE_TAG = 'primary col-sm-9 col-xs-12'
TABLE_HEADER_STRING = 'Data range end'
THREE_WEEK_DELAY = 21


def list_diff(list):
    prev, new_list = 0, []
    for item in list:
        new_list.append(item - prev)
        prev = item
    return new_list


def weekly_average(data):
    return [sum(data[i:i + 7]) // len(data[i:i + 7]) for i in range(0, len(data), 7)]


def pull_items(data, key_name):
    return [data[key][key_name] for key in data.keys()]


def log_items(data_list):
    return [0 if x <= 0 else math.log(x) for x in data_list]


def get_html(url):
    '''
    :param url:
    :return:
    '''
    try:
        html = urlopen(url)
    except HTTPError as e:
        print(e)
    except URLError as _:
        print("server could not be found")
    else:
        return html
    return None


def main():
    data = get_data()
    dates = sorted(list(data.keys()))

    print(dates[-1], data[dates[-1]])
    print(dates[-2], data[dates[-2]])

    cumulative_testing = pull_items(data, 'Total patients approved for testing as of Reporting Date')
    cumulative_cases = pull_items(data, 'Total Cases')
    cumulative_hospitalizations = pull_items(data, 'Number of patients hospitalized with COVID-19')
    cumulative_icu = pull_items(data, 'Number of patients in ICU with COVID-19')
    cumulative_vent = pull_items(data, 'Number of patients in ICU on a ventilator with COVID-19')
    cumulative_deaths = pull_items(data, 'Deaths')

    new_tests = list_diff(cumulative_testing)
    new_cases = list_diff(cumulative_cases)
    new_hospitalizations = list_diff(cumulative_hospitalizations)
    new_icu_cases = list_diff(cumulative_icu)
    new_vent_cases = list_diff(cumulative_vent)
    new_deaths = list_diff(cumulative_deaths)

    plt.style.use('fivethirtyeight')


    positive_rate = [abs(a / (lambda x: 1 if x == 0 else x)(b))*100 for a, b in zip(new_cases[-30:], new_tests[-30:])]
    plt.plot(dates[-len(positive_rate):][-10:], positive_rate[-10:])
    plt.xticks(dates[-len(positive_rate):][-10:], rotation=90)
    plt.yticks(np.arange(0, 20, step=0.5))
    plt.suptitle('Positive Case Rate')
    plt.show()


    weekly_average_deaths = weekly_average(new_deaths)
    weekly_average_cases = weekly_average(new_cases)

    plt.plot(range(1, len(weekly_average_deaths)+1), weekly_average_cases)
    plt.plot(range(1, len(weekly_average_deaths) + 1), weekly_average_deaths)
    plt.suptitle('Weekly Death Rate Vs Case Rate Ontario')
    plt.show()

    plt.plot(range(1, len(weekly_average_deaths) + 1), weekly_average_deaths)
    plt.suptitle('Weekly Death Rate Ontario')
    plt.show()

    log_weekly_cases = log_items(weekly_average(cumulative_cases))
    log_new_weekly_cases = log_items(weekly_average(new_cases))
    spline_curve = UnivariateSpline(log_weekly_cases, log_new_weekly_cases, s=50)
    wxs = np.linspace(0, max(log_weekly_cases), 100)
    wys = spline_curve(wxs)

    plt.rc('xtick', labelsize=8)
    plt.plot(log_weekly_cases, log_new_weekly_cases, '.')
    plt.plot(wxs, wys)
    plt.ylabel('# of cases')
    plt.suptitle('LogLog Weekly Case Rate')
    plt.show()

    log_cases = log_items(cumulative_cases)
    log_new_cases = log_items(new_cases)
    spline_curve = UnivariateSpline(log_cases, log_new_cases, s=100)
    xs = np.linspace(0, max(log_weekly_cases), 200)
    ys = spline_curve(xs)

    plt.rc('xtick', labelsize=8)
    plt.plot(log_cases, log_new_cases, '.')
    plt.plot(xs, ys)
    plt.ylabel('# of cases')
    plt.suptitle('LogLog Daily Case Rate')
    plt.show()

    plt.bar(dates[-10:], new_tests[-10:])
    plt.xticks(dates[-10:], rotation=90)
    plt.suptitle('New Testing Performed')
    plt.show()

    moderate = plt.bar(dates[58:], new_hospitalizations[58:])
    icu = plt.bar(dates[58:], new_icu_cases[58:])
    vent = plt.bar(dates[58:], new_vent_cases[58:])
    plt.xticks(dates[58:], rotation=90)
    plt.suptitle('Hospitalizations')
    plt.legend([moderate, icu, vent], ['Hospital', 'ICU', 'Vent'])
    plt.show()


def get_data():
    '''
    if Ontario's website has not updated the data then read from file, otherwise pull
    the latest data from Ontario's website
    :return: the data set for covid-19 in ontario as a dict
    '''
    date, link = None, ''
    current_date = datetime.datetime.now()
    today = f'{current_date.year}-{str(current_date.month).zfill(2)}-{str(current_date.day).zfill(2)}'
    with open('datefile.txt', 'r') as f:
        last_update_date = f.read()

    if last_update_date != today:
        date, link = check_when_last_updated()

    if date and date != last_update_date:
        print("requesting data")
        r = requests.get(link)
        if r.status_code != 200:
            print(r.status_code)
            return
        f = r.text
        raw_data = f.split('\n')
        data = process_csv_data(raw_data)
        with open('data.txt', 'w') as outfile:
            json.dump(data, outfile)
        with open('datefile.txt', 'w') as f:
            f.write(date)
    else:
        print(date)
        with open('data.txt', 'r') as infile:
            data = json.load(infile)

    return data


def check_when_last_updated():
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


def process_csv_data(raw_data):
    '''
    :param raw_data:
    :return:
    '''
    headers, data = raw_data[0].split(',')[1:], raw_data[1:]
    headers = list(map(lambda x: x.rstrip(), headers))
    data_dict = dict()
    for line in data[:-1]:
        fields = line.split(',')
        date, fields = fields[0], list(map(lambda x: (0 if x in {'', '\n', '\r'} else int(x)), fields[1:]))
        data_dict[date] = dict(zip(headers, fields))
    return data_dict


if __name__ == "__main__":
    main()
