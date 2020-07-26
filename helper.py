from datetime import datetime

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
    current_date = datetime.now()
    month, day = str(current_date.month).zfill(2), str(current_date.day).zfill(2)
    for _month, days in days_in_months_2020.items():
        for _day in range(1, days + 1):
            region[f'2020-{_month}-{_day:02d}'] = 0
            if _month == month and day == str(_day).zfill(2):
                break
        if _month == month:
            break


def get_regional_data(data):
    province, cities = dict(), dict()
    initialize_region_dates(province)
    age_groups = ['<20', '20s', '30s', '40s', '50s', '60s', '70s', '80s', '90s', 'UNKNOWN']
    date_key = 'Accurate_Episode_Date'
    for item in data['data']['features']:
        datum = item['properties']
        if datum['Age_Group'] not in age_groups:
            continue
        if (case_date := datum[date_key]) is None:
            continue

        case_date = case_date[:10]
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

    return province, cities


def new_window_average(data, window_length):
    '''
    :param data: Dictonary with k,v pair Date, Count
    :param window_length: length of the window that will be averaged
    :return: Dictionary with k, v pair Date, average count, date is the last date for the window
    '''
    reverse_chronological_order = list(reversed(data.items()))
    length = len(reverse_chronological_order)
    average = dict()
    for i in range(0, length, window_length):
        window = [item[1] for item in reverse_chronological_order[i:i + window_length]]
        average[reverse_chronological_order[i][0]] = sum(window) / window_length

    return average
