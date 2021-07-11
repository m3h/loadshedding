#!/usr/bin/env python3
# TODO Can replace this with Python's built in logging
def log(txt):
    with open(LOG, 'a') as f:
        f.write('\n')
        f.write('{} {}'.format(datetime.now(), txt))
        f.write(txt)

from datetime import datetime, timedelta
import os
import urllib.request
import ssl
import configuration

# Add support for old TLS
ctx = ssl.create_default_context()
ctx.set_ciphers('DEFAULT@SECLEVEL=1')

from gi.repository import Gtk
import notify2
import pandas as pd

def main():
    curr_stage = try_get_stage(configuration_system['API_URL'])
    date_now = datetime.now()
    sched = pd.read_csv(configuration_user['SCHEDULE_CSV'], sep=';')

    day = str(date_now.day)
    date_tomorrow = date_now + timedelta(days=1)
    day_tomorrow = str(date_tomorrow.day)

    def check_row(row, tomorrow):
        start = time_to_min(row['start'])
        end = time_to_min(row['end'])
        now = time_to_min("{}:{}".format(date_now.hour, date_now.minute))
        # The schedule, and therefore the csv, loops over to 00:30 for the next morning.
        # We wanna compare fairly
        if end < start:
            end += 24*60

        if tomorrow:
            start += 24*60
            end += 24*60
        if start <= now + configuration_system['MIN_OFFSET'] <= end or start <= now + configuration_system['MAX_OFFSET'] <= end:
            # We're shedding now

            if get_override_status(configuration_system['NOTIFICATION_TIMEOUT']):
                txt = 'User cancelled loadshedding cmd "{}"'.format(configuration_user['CMD'])
                log(txt)
                print(txt)
            else:
                txt = 'Executing loadshedding cmd "{}"'.format(configuration_user['CMD'])
                log(txt)
                print(txt)

                os.system(configuration_user['CMD'])
            exit()
        # We're not shedding now
    for _, row in sched.iterrows():
        if not row['stage'] <= curr_stage:
            continue

        if row[day] == configuration_user['AREA']:
            check_row(row, tomorrow=False)

        if row[day_tomorrow] == configuration_user['AREA']:
            check_row(row, tomorrow=True)


def try_get_stage(api_url: str, attempts=20):
    # We'll try x times
    for x in range(attempts):
        try:
            req = urllib.request.urlopen(api_url, timeout=10, context=ctx)
            stage_str = req.read().decode()
            stage = int(stage_str) - 1 # The API has +1

            with open(configuration_system['LOGSTAGE'], 'a') as f:
                f.write('\n')
                f.write("{};{}".format(datetime.now(), stage))
            return stage
        except Exception as e:
            print(str(e))
    print('Failure calling API, after {} attempts'.format(attempts))
    exit()

def time_to_min(time: str):
    hour, minute = [int(x) for x in time.split(':')]

    return hour*60 + minute


def get_override_status(timeout: int):
    override_shutdown = False
    def default_action_cb(n, action):
        nonlocal override_shutdown
        if action == 'default':
            n.close()
            n = notify2.Notification("Cancelling shutdown!")
            n.show()
            print("Cancelling shutdown")
            override_shutdown = True
    def closed_cb(n):
        Gtk.main_quit()

    if not notify2.init("loadshedding.py", mainloop='glib'):
        return True
    n = notify2.Notification("Cancel loadshedding shutdown?")

    server_capabilities = notify2.get_server_caps()
    if 'actions' in server_capabilities:
        n.add_action('default', "Cancel shutdown", default_action_cb)
    n.connect('closed', closed_cb)

    n.timeout = timeout*1000
    n.set_urgency(notify2.URGENCY_CRITICAL)
    if not n.show():
        return True

    Gtk.main()
    return override_shutdown

if __name__ == "__main__":
    try:
        configuration_system = configuration.read_configuration_system('configuration_system.yaml')
    except FileNotFoundError as e:
        LOG = 'crash_log.log'
        txt = f'Configuration file does not exist\n\t{str(e)}'
        print(txt)
        log(txt)
        exit()
    except configuration.MissingKeyError as e:
        LOG = 'crash_log.log'
        txt = str(e)
        print(txt)
        log(txt)
        exit()

    LOG = configuration_system['LOG']

    try:
        configuration_user = configuration.read_configuration_user('configuration_user.yaml')
    except FileNotFoundError as e:
        txt = f'Configuration file does not exist\n\t{str(e)}'
        log(txt)
        exit()
    except configuration.MissingKeyError as e:
        txt = str(e)
        print(txt)
        log(txt)
        exit()

    main()
