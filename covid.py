from json import load
from math import log
from datetime import datetime
import matplotlib.pyplot as plt
from helper import get_regional_data, window_average
from fetch import get_date_and_data, save_data_to_file, text_to_kv_pair, ONTARIO_COVID19_GEOJSON, ONTARIO_COVID19_CSV, \
    ONTARIO_COVID19_POS_LINK, ONTARIO_COVID19_STATUS_LINK
from rt import *
from reddit import send_update
import csv
import asciichartpy

THREE_WEEK_DELAY = 21
WINDOW_SIZE = 5
LAST_N_DAYS = (WINDOW_SIZE * 7) + 1
FIRST_N_WEEKS = (LAST_N_DAYS // WINDOW_SIZE) + 1


def generate_plots_of(keys, data_set, dates):
    plots = []
    for key in keys:
        itr = cumulative_to_daily([item[key] for item in data_set])
        plot = {
            'name': key,
            'data': dict(zip(dates, itr)),
            'avg_data': window_average(dict(zip(dates, itr)), WINDOW_SIZE),
        }
        plots.append(plot)
    return {'plots': plots, 'dates': dates}


def make_plots(plot_title, plots):
    plts, dates = plots['plots'], plots['dates']
    for plot in plts:
        plt.scatter(list(plot['data'].keys())[-LAST_N_DAYS:], list(plot['data'].values())[-LAST_N_DAYS:],
                    label=plot['name'], alpha=0.7)
        plt.plot(list(plot['avg_data'].keys())[:FIRST_N_WEEKS], list(plot['avg_data'].values())[:FIRST_N_WEEKS],
                 label=f'{plot["name"]} Average', alpha=0.7)

    plt.xticks(dates[-LAST_N_DAYS:], rotation=90)
    plt.suptitle(plot_title)
    plt.legend()
    plt.show()


def cumulative_to_daily(values):
    result = [values[i + 1] - values[i] for i in range(0, len(values) - 1)]
    result.insert(0, values[0])
    return result


def service_update(today):
    ontario_data = get_date_and_data(today, ONTARIO_COVID19_STATUS_LINK, ONTARIO_COVID19_CSV)
    if (date := ontario_data['date']) == today:
        save_data_to_file(date, ontario_data['data'], ONTARIO_COVID19_CSV)

    ontario_case_data = get_date_and_data(today, ONTARIO_COVID19_POS_LINK, ONTARIO_COVID19_GEOJSON)
    if (date := ontario_case_data['date']) == today:
        save_data_to_file(date, ontario_case_data['data'], ONTARIO_COVID19_GEOJSON)

    ontario, cities = get_regional_data(ontario_case_data)
    if date == today:
        with open('ef_ont.csv', 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['date', 'positive'])
            for key, value in ontario.items():
                writer.writerow([key, value])

    with open('ef_ont.csv', 'r') as f:
        ontario_rt = pd.read_csv(f,
                                 usecols=['date', 'positive'],
                                 parse_dates=['date'],
                                 index_col=['date'],
                                 squeeze=True).sort_index()

    ontario_rt = ontario_rt.iloc[50:-7]
    cases = ontario_rt.rename("ON cases")
    cases.index.names = ['date']
    result = calculate_rt(cases)

    ontario_values = ontario_data['data'].values()
    ontario_dates = list(ontario_data['data'].keys())

    daily_plots = generate_plots_of(['Deaths', 'Total Cases'], ontario_values, ontario_dates)
    hospital_plots = generate_plots_of(['Number of patients hospitalized with COVID-19',
                                        'Number of patients in ICU with COVID-19',
                                        'Number of patients in ICU on a ventilator with COVID-19'],
                                       ontario_values, ontario_dates)

    ta = 'Total patients approved for testing as of Reporting Date'
    cp = 'Total Cases'
    yd = ontario_data['data'][ontario_dates[-2]]
    td = ontario_data['data'][ontario_dates[-1]]
    positivity_rate = 100 * ((td[cp] - yd[cp]) / (td[ta] - yd[ta]))

    POPULATION_ONTARIO = 14446515
    H100k = 100000
    avg = window_average(ontario, WINDOW_SIZE)
    cases_per_100k = (list(avg.values())[1] / POPULATION_ONTARIO) * H100k

    data = {
        'today_key_info': {
            'case count': (td[cp] - yd[cp]),
            'test count': (td[ta] - yd[ta]),
            'date': today,
            'r_t': result.iloc[-1]['ML'],
            'case per 100k': cases_per_100k,
            'positivity': positivity_rate
        },
        'plots': {
            'rt': result['ML'].tolist()
        }
    }

    return data


def main():
    current_date = datetime.now()
    year, month, day = current_date.year, str(current_date.month).zfill(2), str(current_date.day).zfill(2)
    today = f'{year}-{month}-{day}'

    ontario_data = get_date_and_data(today, ONTARIO_COVID19_STATUS_LINK, ONTARIO_COVID19_CSV)
    if (date := ontario_data['date']) == today:
        save_data_to_file(date, ontario_data['data'], ONTARIO_COVID19_CSV)

    ontario_case_data = get_date_and_data(today, ONTARIO_COVID19_POS_LINK, ONTARIO_COVID19_GEOJSON)
    if (date := ontario_case_data['date']) == today:
        save_data_to_file(date, ontario_case_data['data'], ONTARIO_COVID19_GEOJSON)

    ontario, cities = get_regional_data(ontario_case_data)
    if date == today:
        with open('ef_ont.csv', 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['date', 'positive'])
            for key, value in ontario.items():
                writer.writerow([key, value])

    with open('ef_ont.csv', 'r') as f:
        ontario_rt = pd.read_csv(f,
                                 usecols=['date', 'positive'],
                                 parse_dates=['date'],
                                 index_col=['date'],
                                 squeeze=True).sort_index()

    ontario_rt = ontario_rt.iloc[50:-7]
    cases = ontario_rt.rename("ON cases")
    cases.index.names = ['date']
    result = calculate_rt(cases)

    ontario_values = ontario_data['data'].values()
    ontario_dates = list(ontario_data['data'].keys())

    daily_plots = generate_plots_of(['Deaths', 'Total Cases'], ontario_values, ontario_dates)
    hospital_plots = generate_plots_of(['Number of patients hospitalized with COVID-19',
                                        'Number of patients in ICU with COVID-19',
                                        'Number of patients in ICU on a ventilator with COVID-19'],
                                       ontario_values, ontario_dates)

    ta = 'Total patients approved for testing as of Reporting Date'
    cp = 'Total Cases'
    yd = ontario_data['data'][ontario_dates[-2]]
    td = ontario_data['data'][ontario_dates[-1]]
    positivity_rate = 100 * ((td[cp] - yd[cp]) / (td[ta] - yd[ta]))

    POPULATION_ONTARIO = 14446515
    H100k = 100000
    avg = window_average(ontario, WINDOW_SIZE)
    cases_per_100k = (list(avg.values())[1] / POPULATION_ONTARIO) * H100k
    print(f'{cases_per_100k:2.2f} cases per 100,000')
    print(f'{positivity_rate:2.2f}% positivity rate')
    print(result.iloc[-1])

    case_plots = {
        'plots': [
            {
                'name': 'Hamilton',
                'data': cities['Hamilton'],
                'avg_data': window_average(cities['Hamilton'], WINDOW_SIZE)
            },
            {
                'name': 'Oakville',
                'data': cities['Oakville'],
                'avg_data': window_average(cities['Oakville'], WINDOW_SIZE)
            },
            {
                'name': 'Windsor',
                'data': cities['Windsor'],
                'avg_data': window_average(cities['Windsor'], WINDOW_SIZE)
            },
            {
                'name': 'Sarnia/Lambton',
                'data': cities['Point Edward'],
                'avg_data': window_average(cities['Point Edward'], WINDOW_SIZE)
            },
            {
                'name': 'Ontario',
                'data': ontario,
                'avg_data': window_average(ontario, WINDOW_SIZE)
            }
        ],
        'dates': list(ontario.keys())
    }

    arg = input('Continue? Y/[N] ')
    if arg[0].lower() != 'y':
        return 0

    fig, ax = plt.subplots(figsize=(1200 / 72, 800 / 72))
    plot_rt(result, fig, ax, 'ON')
    ax.set_title(f'Real-time $R_t$ for ON')
    ax.xaxis.set_major_locator(mdates.WeekdayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    plt.show()

    make_plots('Deaths in Ontario', daily_plots)
    make_plots('Ontario Hospital Status', hospital_plots)
    make_plots('Weekly Average', case_plots)


if __name__ == "__main__":
    main()
