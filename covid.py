from json import load
from math import log
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import UnivariateSpline
from fetch import get_date_and_data, save_data_to_file

THREE_WEEK_DELAY = 21


def list_diff(items):
    prev, new_list = 0, []
    for item in items:
        new_list.append(item - prev)
        prev = item
    return new_list


def window_average(data, window):
    return [sum(data[i:i + window]) // len(data[i:i + window]) for i in range(0, len(data), window)]


def pull_items(data, key_name):
    return [data[key][key_name] for key in data.keys()]


def log_items(data_list):
    return [0 if x <= 0 else log(x) for x in data_list]


def main():
    current_date = datetime.now()
    today = f'{current_date.year}-{str(current_date.month).zfill(2)}-{str(current_date.day).zfill(2)}'
    date, data = get_date_and_data(today)
    if date == today:
        save_data_to_file(date, data)


    dates = sorted(list(data.keys()))

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

    positive_rate = [abs(a / (1 if b == 0 else b)) * 100 for a, b in zip(new_cases[-30:], new_tests[-30:])]
    plt.plot(dates[-len(positive_rate):][-10:], positive_rate[-10:])
    plt.xticks(dates[-len(positive_rate):][-10:], rotation=90)
    plt.yticks(np.arange(0, max(positive_rate[-10:]), step=0.25))
    plt.suptitle('Positive Case Rate')
    plt.show()

    def plot_data(plotter, y_data, x_data=None, title=None):
        for item in y_data:
            plotter.plot(x_data if x_data else range(1, len(item) + 1), item)
        if title:
            plotter.suptitle(title)

        plt.xticks(x_data if x_data else range(1, len(item) + 1), rotation=90)
        plt.show()

    plot_data(plt, [window_average(new_cases, 7), window_average(new_deaths, 7)], title='Weekly Death Rate Vs Case Rate Ontario')
    plot_data(plt, [new_deaths[-30:]], x_data=dates[-30:], title='Daily Fatalities, Ontario')


    log_weekly_cases = log_items(window_average(cumulative_cases, 4))
    log_new_weekly_cases = log_items(window_average(new_cases, 4))
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

    with open('conposcovidloc.geojson', 'r') as infile:
        data = load(infile)
        list_of = data['features']
        count = dict()
        count['unknown'] = 0
        key = 'Accurate_Episode_Date'  # 'Age_Group' # 'Accurate_Episode_Date'
        for item in list_of:
            datum = item['properties']
            # if datum['Outcome1'] == 'Fatal':
            # if datum['Reporting_PHU_City'] == 'Hamilton':
            if (case := datum[key]) is None:
                continue
            if case not in count:
                count[case] = 1
            else:
                count[case] += 1

    date_counts = list(map(list, zip(*sorted(count.items(), key=lambda x: x[0]))))

    dates = list(map(lambda x: x[:10], date_counts[0]))
    plt.bar(dates, date_counts[1])
    plt.xticks(dates, rotation=90)
    plt.show()


if __name__ == "__main__":
    main()
