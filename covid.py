from json import load
from math import log
from datetime import datetime
import matplotlib.pyplot as plt
from helper import get_regional_data, new_window_average
from fetch import get_date_and_data, save_data_to_file, text_to_kv_pair, ONTARIO_COVID19_GEOJSON, ONTARIO_COVID19_CSV, \
    ONTARIO_COVID19_POS_LINK, ONTARIO_COVID19_STATUS_LINK

THREE_WEEK_DELAY = 21


def list_diff(items):
    prev, new_list = 0, []
    for item in items:
        new_list.append(item - prev)
        prev = item
    return new_list


def window_average(data, window):
    reversed_data = list(reversed(data))
    reversed_data = [sum(reversed_data[i:i + window]) / len(reversed_data[i:i + window]) for i in
                     range(0, len(data), window)]
    return list(reversed(reversed_data))


def pull_items(data, key_name):
    return [data[key][key_name] for key in data.keys()]


def log_items(data_list):
    return [0 if x <= 0 else log(x) for x in data_list]


def main():
    current_date = datetime.now()
    year, month, day = current_date.year, str(current_date.month).zfill(2), str(current_date.day).zfill(2)
    today = f'{year}-{month}-{day}'
    date, data = get_date_and_data(today, ONTARIO_COVID19_STATUS_LINK, ONTARIO_COVID19_CSV)

    if date == today:
        save_data_to_file(date, data, ONTARIO_COVID19_CSV)

    geojson_date, geojson_data = get_date_and_data(today, ONTARIO_COVID19_POS_LINK, ONTARIO_COVID19_GEOJSON)
    if geojson_date == today:
        save_data_to_file(geojson_date, geojson_data, ONTARIO_COVID19_GEOJSON)

    arg = input('Continue? Y/[N] ')
    if arg[0].lower() != 'y':
        return 0

    print(geojson_data['features'][0]['properties'].keys())

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

    plt.bar(dates[-42:], new_cases[-42:])
    plt.xticks(dates[-42:], rotation=90)
    plt.show()

    positive_rate = [abs(a / (1 if b == 0 else b)) * 100 for a, b in zip(new_cases[-30:], new_tests[-30:])]
    plt.plot(dates[-len(positive_rate):][-10:], positive_rate[-10:])
    plt.xticks(dates[-len(positive_rate):][-10:], rotation=90)

    step_size = 0.5
    inverse_step_size = 1 / step_size
    range_end = int(inverse_step_size * max(positive_rate[-10:]) + 1)
    range_start = int(inverse_step_size * min(positive_rate[-10:]) - 1)
    plt.yticks([i * step_size for i in range(range_start, range_end)])
    plt.suptitle('Positive Case Rate')
    plt.show()

    def plot_data(plotter, y_data, x_data=None, title=None):
        y = {}
        for y in y_data:
            plotter.plot(x_data if x_data else range(1, len(y) + 1), y)
        if title:
            plotter.suptitle(title)

        plt.xticks(x_data if x_data else range(1, len(y) + 1), rotation=90)
        plt.show()

    plot_data(plt, [window_average(new_cases, 7), window_average(new_deaths, 7)],
              title='Weekly Death Rate Vs Case Rate Ontario')
    plot_data(plt, [new_deaths[-30:]], x_data=dates[-30:], title='Daily Fatalities, Ontario')


    last_n_days = 14
    moderate = plt.bar(dates[-last_n_days:], new_hospitalizations[-last_n_days:])
    icu = plt.bar(dates[-last_n_days:], new_icu_cases[-last_n_days:])
    vent = plt.bar(dates[-last_n_days:], new_vent_cases[-last_n_days:])
    plt.xticks(dates[-last_n_days:], rotation=90)
    plt.suptitle('Hospitalizations')
    plt.legend([moderate, icu, vent], ['Hospital', 'ICU', 'Vent'])
    plt.show()

    ontario, cities = get_regional_data(geojson_data)
    print(ontario)
    print(cities['Hamilton'])

    plots = [
        {
            'name': 'Hamilton',
            'data': cities['Hamilton'],
            'avg_data': new_window_average(cities['Hamilton'], 7)
        },
        {
            'name': 'Oakville',
            'data': cities['Oakville'],
            'avg_data': new_window_average(cities['Oakville'], 7)
        },
        {
            'name': 'Windsor',
            'data': cities['Windsor'],
            'avg_data': new_window_average(cities['Windsor'], 7)
        },
        {
            'name': 'Sarnia/Lambton',
            'data': cities['Point Edward'],
            'avg_data': new_window_average(cities['Point Edward'], 7)
        },
        {
            'name': 'Ontario',
            'data': ontario,
            'avg_data': new_window_average(ontario, 7)
        }
    ]

    LAST_N_DAYS = 35 + 1
    FIRST_N_WEEKS = (LAST_N_DAYS // 7) + 1
    dates = list(ontario.keys())

    for place in plots:
        plt.scatter(list(place['data'].keys())[-LAST_N_DAYS:], list(place['data'].values())[-LAST_N_DAYS:],
            label=place['name'], alpha=0.7)
        plt.plot(list(place['avg_data'].keys())[:FIRST_N_WEEKS], list(place['avg_data'].values())[:FIRST_N_WEEKS],
             label=f'{place["name"]} AVG', alpha=0.7)

    plt.xticks(dates[-LAST_N_DAYS:], rotation=90)
    plt.suptitle("Weekly average")
    plt.legend()
    plt.show()


if __name__ == "__main__":
    main()
