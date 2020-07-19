from json import load
from math import log
from datetime import datetime
import matplotlib.pyplot as plt
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
    reversed_data = [sum(reversed_data[i:i + window]) // len(reversed_data[i:i + window]) for i in
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
        for y in y_data:
            plotter.plot(x_data if x_data else range(1, len(y) + 1), y)
        if title:
            plotter.suptitle(title)

        plt.xticks(x_data if x_data else range(1, len(y) + 1), rotation=90)
        plt.show()

    plot_data(plt, [window_average(new_cases, 7), window_average(new_deaths, 7)],
              title='Weekly Death Rate Vs Case Rate Ontario')
    plot_data(plt, [new_deaths[-30:]], x_data=dates[-30:], title='Daily Fatalities, Ontario')

    """
    log_weekly_cases = log_items(window_average(cumulative_cases, 7))
    log_new_weekly_cases = log_items(window_average(new_cases, 7))


    plt.rc('xtick', labelsize=8)
    plt.plot(log_weekly_cases, log_new_weekly_cases, '.')
    plt.ylabel('# of cases')
    plt.suptitle('LogLog Weekly Case Rate')
    plt.show()

    plt.bar(dates[-10:], new_tests[-10:])
    plt.xticks(dates[-10:], rotation=90)
    plt.suptitle('New Testing Performed')
    plt.show()
    """

    last_n_days = 14
    moderate = plt.bar(dates[-last_n_days:], new_hospitalizations[-last_n_days:])
    icu = plt.bar(dates[-last_n_days:], new_icu_cases[-last_n_days:])
    vent = plt.bar(dates[-last_n_days:], new_vent_cases[-last_n_days:])
    plt.xticks(dates[-last_n_days:], rotation=90)
    plt.suptitle('Hospitalizations')
    plt.legend([moderate, icu, vent], ['Hospital', 'ICU', 'Vent'])
    plt.show()

    days_in_months_2020 = {
        '01': 31,
        '02': 29,
        '03': 31,
        '04': 30,
        '05': 31,
        '06': 30,
        '07': 31,
        '08': 31,
        '09': 30,
        '10': 31,
        '11': 30,
        '12': 31
    }

    def initialize_region_dates(region):
        for _month, days in days_in_months_2020.items():
            for _day in range(1, days + 1):
                region[f'2020-{_month}-{_day:02d}'] = 0
                if _month == month and day == str(_day).zfill(2):
                    break
            if _month == month:
                break

    province = dict()
    initialize_region_dates(province)

    age_groups = ['<20', '20s', '30s', '40s', '50s', '60s', '70s', '80s', '90s', 'UNKNOWN']

    cities = dict()
    date_key = 'Accurate_Episode_Date'
    for item in geojson_data['features']:
        datum = item['properties']
        if datum['Age_Group'] not in age_groups:
            continue
        if (case_date := datum[date_key]) is None:
            continue
        if case_date not in province:
            province[case_date] = 1
        else:
            province[case_date] += 1

        if (city := datum['Reporting_PHU_City']) not in cities:
            cities[city] = dict()
            initialize_region_dates(cities[city])

        current_city = cities[city]
        if case_date not in cities[city]:
            current_city[case_date] = 1
        else:
            current_city[case_date] += 1

    print(cities.keys())

    def get_city_count(city_name):
        return list(zip(*sorted(cities[city_name].items(), key=lambda item: item[0])))

    province_counts = list(zip(*sorted(province.items(), key=lambda item: item[0])))
    hamilton_counts = get_city_count('Hamilton')
    oakville_counts = get_city_count('Oakville')
    windsor_counts = get_city_count('Windsor')

    dates = list(map(lambda x: x[:10], province_counts[0]))
    hamilton_average_cases = window_average(hamilton_counts[1][-89:-5], 7)
    oakville_average_cases = window_average(oakville_counts[1][-89:-5], 7)
    windsor_average_cases = window_average(windsor_counts[1][-89:-5], 7)
    province_average_cases = window_average(province_counts[1][-89:-5], 7)
    top_range = max(province_average_cases[-12:])
    weeks = [x for x in range(1, len(hamilton_average_cases) + 1)]
    plt.plot(weeks, hamilton_average_cases, label='Hamilton')
    plt.plot(weeks, oakville_average_cases, label='Halton')
    plt.plot(weeks, windsor_average_cases, label='Windsor')
    plt.plot(weeks, province_average_cases, label='Ontario')
    plt.yticks([i for i in range(0, top_range+5, 5)])
    plt.suptitle("Weekly average")
    plt.legend()
    plt.show()

    ont = plt.bar(dates[-42:], province_counts[1][-42:])
    ham = plt.bar(dates[-42:], hamilton_counts[1][-42:])
    plt.xticks(dates[-42:], rotation=90)
    plt.suptitle("Case Count vs Effective Case Date")
    plt.legend([ham, ont], ['Hamilton', 'Ontario'])
    plt.show()

    '''
    other_counts = list(map(list, zip(*sorted(other.items(), key=lambda x: x[0]))))
    other_dates = list(map(lambda x: x[:10], other_counts[0]))
    plt.bar(other_dates[-42:], other_counts[1][-42:])
    plt.xticks(other_dates[-42:], rotation=90)
    plt.show()
    '''


if __name__ == "__main__":
    main()
