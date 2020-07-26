from json import load
from math import log
from datetime import datetime
import matplotlib.pyplot as plt
from helper import get_regional_data, new_window_average
from fetch import get_date_and_data, save_data_to_file, text_to_kv_pair, ONTARIO_COVID19_GEOJSON, ONTARIO_COVID19_CSV, \
    ONTARIO_COVID19_POS_LINK, ONTARIO_COVID19_STATUS_LINK
from rt import *

THREE_WEEK_DELAY = 21
WINDOW_SIZE = 5
LAST_N_DAYS = (WINDOW_SIZE * 7) + 1
FIRST_N_WEEKS = (LAST_N_DAYS // WINDOW_SIZE) + 1


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

    arg = input('Continue? Y/[N] ')
    if arg[0].lower() != 'y':
        return 0

    ontario, cities = get_regional_data(ontario_case_data)

    with open('ont.csv', 'r') as f:
        ontario_rt = pd.read_csv(f,
                                 usecols=['Reported Date', 'Total Cases'],
                                 parse_dates=['Reported Date'],
                                 index_col=['Reported Date'],
                                 squeeze=True).sort_index()

    cases = ontario_rt.rename("ON cases")
    cases.index.names = ['date']
    result = calculate_rt(cases)
    fig, ax = plt.subplots(figsize=(1200 / 72, 800 / 72))
    plot_rt(result, fig, ax, 'ON')
    ax.set_title(f'Real-time $R_t$ for ON')
    ax.xaxis.set_major_locator(mdates.WeekdayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    plt.show()


    ontario_values = ontario_data['data'].values()
    ontario_dates = list(ontario_data['data'].keys())

    deaths_itr = cumulative_to_daily([item['Deaths'] for item in ontario_values])
    deaths = dict(zip(ontario_dates, deaths_itr))
    avg_deaths = new_window_average(dict(zip(ontario_dates, deaths_itr)), WINDOW_SIZE)

    positives_itr = cumulative_to_daily([item['Total Cases'] for item in ontario_values])
    postives = dict(zip(ontario_dates, positives_itr))
    avg_positives = new_window_average(dict(zip(ontario_dates, positives_itr)), WINDOW_SIZE)

    daily_plots = {
        'plots': [
            {
                'name': 'Deaths in Ontario',
                'data': deaths,
                'avg_data': avg_deaths
            },
            {
                'name': 'Daily Positive Count',
                'data': postives,
                'avg_data': avg_positives
            }
        ],
        'dates': ontario_dates
    }

    make_plots('Deaths in Ontario', daily_plots)
    hospital_itr = [item['Number of patients hospitalized with COVID-19'] for item in ontario_values]
    hospitalizations = dict(zip(ontario_dates, hospital_itr))
    avg_hospitalizations = new_window_average(dict(zip(ontario_dates, hospital_itr)), WINDOW_SIZE)

    icu_itr = [item['Number of patients in ICU with COVID-19'] for item in ontario_values]
    icu = dict(zip(ontario_dates, icu_itr))
    avg_icu = new_window_average(dict(zip(ontario_dates, icu_itr)), WINDOW_SIZE)

    ventilator_itr = [item['Number of patients in ICU on a ventilator with COVID-19'] for item in ontario_values]
    ventilator = dict(zip(ontario_dates, ventilator_itr))
    avg_ventilator = new_window_average(dict(zip(ontario_dates, ventilator_itr)), WINDOW_SIZE)

    hospital_plots = {
        'plots': [
            {
                'name': 'Number of patients hospitalized',
                'data': hospitalizations,
                'avg_data': avg_hospitalizations
            },
            {
                'name': 'Number of patients in ICU',
                'data': icu,
                'avg_data': avg_icu
            },
            {
                'name': 'Number of patients on a ventilator',
                'data': ventilator,
                'avg_data': avg_ventilator
            },
        ],
        'dates': ontario_dates
    }

    make_plots('Ontario Hospital Status', hospital_plots)

    case_plots = {
        'plots': [
            {
                'name': 'Hamilton',
                'data': cities['Hamilton'],
                'avg_data': new_window_average(cities['Hamilton'], WINDOW_SIZE)
            },
            {
                'name': 'Oakville',
                'data': cities['Oakville'],
                'avg_data': new_window_average(cities['Oakville'], WINDOW_SIZE)
            },
            {
                'name': 'Windsor',
                'data': cities['Windsor'],
                'avg_data': new_window_average(cities['Windsor'], WINDOW_SIZE)
            },
            {
                'name': 'Sarnia/Lambton',
                'data': cities['Point Edward'],
                'avg_data': new_window_average(cities['Point Edward'], WINDOW_SIZE)
            },
            {
                'name': 'Ontario',
                'data': ontario,
                'avg_data': new_window_average(ontario, WINDOW_SIZE)
            }
        ],
        'dates': list(ontario.keys())
    }

    make_plots('Weekly Average', case_plots)


if __name__ == "__main__":
    main()
