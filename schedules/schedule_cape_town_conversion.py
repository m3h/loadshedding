"""Cape Town conversion script from the intermediate format to the `loadshedding` schedule format.

Some aspects (time intervals) are hardcoded since this is hopefully a once-off
Needs to be double checked if new schedules are released

To fix the hardcoded aspects:
    - Automatically calculate the time intervals from the input workbook
"""
import string
import datetime

import pandas as pd
import openpyxl

if __name__ == '__main__':
    input_workbook = 'schedules/schedule_intermediate_city_of_cape_town.xlsx'
    output_csv = 'schedules/load_shedding_city_of_cape_town.csv'

    # Setup the output datastructure in pandas
    interval_start = range(0, 24, 2)
    interval_length = datetime.timedelta(hours=2, minutes=30)
    stages = range(1, 8 + 1)
    days = range(1, 31 + 1)

    header = ['start', 'end', 'stage', ] + list(days)
    data = []
    for time_start in interval_start:
        start = datetime.time(hour=time_start)
        end = (datetime.datetime.combine(datetime.date.today(), start) + interval_length).time()

        for stage in stages:
            d = [start, end, stage, ] + [None, ]*len(days)
            data.append(d)

    data = data

    df = pd.DataFrame(data, columns=header)

    # Parse the input workbook and add to dataframe
    workbook = openpyxl.load_workbook(input_workbook)
    worksheets = [workbook[f'Sheet{stage}'] for stage in stages]

    for i, time_start in enumerate(interval_start):
        index_wb_row = str(i + 3)

        start = datetime.time(hour=time_start)
        end = (datetime.datetime.combine(datetime.date.today(), start) + interval_length).time()

        for j, day in enumerate(range(1, 16 + 1)):
            index_wb_column = string.ascii_uppercase[j + 2]

            # The same schedule is shared between two days each month with an offset of 16 days
            days_both = [day, ] + ([day + 16] if day < 16 else [])

            # We need to find the new area for each day
            areas = set()
            for stage, worksheet in zip(stages, worksheets):
                v = worksheet[index_wb_column + index_wb_row].value
                v = set(int(a.strip()) for a in v.split(',')) if not(isinstance(v, int)) else set((v, ))
                a = v - areas
                assert(len(a) == 1)
                a = a.pop()

                row = df.loc[(df['start'] == start) & (df['end'] == end) & (df['stage'] == stage)]
                assert(len(row) == 1)

                for day in days_both:
                    loc = row.loc[:, day]
                    assert(len(loc.values) == 1)
                    assert(loc.values[0] is None)

                    df.loc[(df['start'] == start) & (df['end'] == end) & (df['stage'] == stage), day] = a

                areas.add(a)

    df.to_csv(output_csv, index=False, sep=';')