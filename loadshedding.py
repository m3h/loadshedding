#!/usr/bin/env python3
import logging
from datetime import datetime, timedelta
import os
import urllib.request
import ssl

import pandas as pd

import configuration

import lutils.tktimeoutdialog
# Add support for old TLS
ctx = ssl.create_default_context()
ctx.set_ciphers('DEFAULT@SECLEVEL=1')


def main():
    curr_stage = try_get_stage(configuration_system['API_URL'])
    date_now = datetime.now()
    sched = pd.read_csv(configuration_user['SCHEDULE_CSV'], sep=';')

    shedding = check_shedding(
        curr_stage, sched, configuration_user, configuration_system, date_now
        )

    if not shedding:
        return False

    if configuration_user['GTK_NOTIFICATION']:
        override, reason = get_override_status(
            configuration_system['NOTIFICATION_TIMEOUT'],
            "Loadshedding imminent!")
    else:
        override, reason = False, None

    if override:
        message = 'User cancelled loadshedding ({}) cmd "{}"'.format(
            reason,
            configuration_user['CMD'])
        logger.info(message)
    else:
        message = 'Executing loadshedding cmd "{}"'.format(
            configuration_user['CMD'])
        logger.info(message)

        os.system(configuration_user['CMD'])
    exit()


def check_row(row, date_now, tomorrow, configuration_system):
    start = time_to_min(row['start'])
    end = time_to_min(row['end'])
    now = time_to_min("{}:{}".format(date_now.hour, date_now.minute))
    # The schedule, and therefore the csv,
    # loops over to 00:30 for the next morning.
    # We wanna compare fairly
    if end < start:
        end += 24*60

    if tomorrow:
        start += 24*60
        end += 24*60
    if (start <= now + configuration_system['MIN_OFFSET'] <= end or
            start <= now + configuration_system['MAX_OFFSET'] <= end):
        # We're shedding now
        return True

    return False


def check_shedding(
        curr_stage, sched, configuration_user, configuration_system, date_now):
    day = str(date_now.day)
    date_tomorrow = date_now + timedelta(days=1)
    day_tomorrow = str(date_tomorrow.day)

    for _, row in sched.iterrows():
        if not row['stage'] <= curr_stage:
            continue

        if (row[day] == configuration_user['AREA'] and
                check_row(row, date_now, False, configuration_system)):
            return True

        if (row[day_tomorrow] == configuration_user['AREA']
                and check_row(row, date_now, True, configuration_system)):
            return True

    return False


def try_get_stage(api_url: str, attempts=20):
    # We'll try x times
    for x in range(attempts):
        try:
            req = urllib.request.urlopen(api_url, timeout=10, context=ctx)
            stage_str = req.read().decode()
            stage = int(stage_str) - 1  # The API has +1

            logger_stage.info(f'{stage}')

            return stage
        except Exception as e:
            logger.warning(str(e))
    logger.error('Failure calling API, after {} attempts'.format(attempts))
    exit()


def time_to_min(time: str):
    hour, minute = [int(x) for x in time.split(':')][:2]

    return hour*60 + minute


def get_override_status(timeout: int, dialog_msg: str):

    dialog_notification = lutils.tktimeoutdialog.TkTimeoutDialog()

    shutdown, reason = dialog_notification.show_notification(
        dialog_msg=dialog_msg,
        timeout=timeout,
        affirmative_txt='Shutdown')

    override_shutdown = not shutdown
    return override_shutdown, reason


if __name__ == "__main__":
    def get_logger(name, filename):
        logger_crash = logging.getLogger(name)
        logger_crash.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        logger_crash.addHandler(ch)
        fh = logging.FileHandler(filename)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger_crash.addHandler(fh)
        return logger_crash

    def get_crash_logger():
        return get_logger('crash', 'crash.log')

    logger_crash = get_crash_logger()

    try:
        configuration_system = configuration.read_configuration_system(
            'configuration_system.yaml')
    except FileNotFoundError as e:

        message = f'Configuration file does not exist\n\t{str(e)}'
        logger_crash.critical(message)
        exit()
    except configuration.MissingKeyError as e:
        message = str(e)
        logger_crash.critical(message)
        exit()

    logger = get_logger('general', configuration_system['LOG'])
    logger_stage = get_logger('stage', configuration_system['LOGSTAGE'])

    try:
        configuration_user = configuration.read_configuration_user(
            'configuration_user.yaml')
    except FileNotFoundError as e:
        message = f'Configuration file does not exist\n\t{str(e)}'
        logger.critical(message)
        logger_crash.critical(message)
        exit()
    except configuration.MissingKeyError as e:
        message = str(e)
        logger.critical(message)
        logger_crash.critical(message)
        exit()

    main()
