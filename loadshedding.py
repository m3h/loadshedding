#!/usr/bin/env python3
AREA='3A'
MIN_OFFSET = 4 # minutes
MAX_OFFSET = 7 # minutes
CMD = "sudo /usr/sbin/s2disk"

API_URL = "http://loadshedding.eskom.co.za/LoadShedding/GetStatus"

SCHEDULE_CSV = '/home/reece/scripts/loadshedding/load_shedding_cp.csv'
LOGSTAGE = "/home/reece/scripts/loadshedding/stagelog.txt"
LOG = "/home/reece/scripts/loadshedding/log.log"

def log(txt):
    with open(LOG, 'a') as f:
        f.write('\n')
        f.write(txt)

from datetime import datetime, timedelta
import os
import urllib.request

import pandas as pd

def main():
    curr_stage = try_get_stage(API_URL)
    date_now = datetime.now()
    sched = pd.read_csv(SCHEDULE_CSV, sep=';')

    day = str(date_now.day)
    sched_s = sched[sched['stage'] <= curr_stage]
    sched_d_a = sched_s[sched_s[day] == AREA]
    for start_s, end_s in zip(sched_d_a['start'], sched_d_a['end']):
        start = time_to_min(start_s)
        end = time_to_min(end_s)
        now = time_to_min("{}:{}".format(date_now.hour, date_now.minute))
        # The schedule, and therefore the csv, loops over to 00:30 for the next morning.
        # We wanna comparse fairly
        if end < start:
            end += 24*60

        if start <= now + MIN_OFFSET <= end or start <= now + MAX_OFFSET <= end:
            # We're shedding now
            txt = 'Executing loadshedding cmd "{}"'.format(CMD)
            log(txt)
            print(txt)
            os.system(CMD)
            exit()
    # We're not shedding now


def try_get_stage(api_url: str, attempts=20):
    # We'll try x times
    for x in range(attempts):
        try:
            req = urllib.request.urlopen(api_url, timeout=1)
            stage_str = req.read().decode()
            stage = int(stage_str) - 1 # The API has +1

            with open(LOGSTAGE, 'a') as f:
                f.write('\n')
                f.write("{};{}".format(datetime.now(), stage))
            return stage
        except:
            pass
    print('Failure calling API, after {} attempts'.format(attempts))
    exit()

def time_to_min(time: str):
    hour, minute = [int(x) for x in time.split(':')]

    return hour*60 + minute


if __name__ == "__main__":
    main()
