#!/usr/bin/env python3
import logging
import logging.handlers
from datetime import datetime, timedelta
import os
import urllib.request
import json
import pathlib

import loadshedding_thingamabob.schedule

import configuration
import lutils.lcsv
import lutils.tktimeoutdialog


def main(
        configuration_system: dict, configuration_user: dict,
        logger: logging.Logger, logger_stage: logging.Logger
        ):
    logger.info(
        'Running loadshedding script: '
        f'configuration_system={configuration_system} '
        f'configuration_user={configuration_user} '
        )

    response = get_stage_schedule(configuration_user['API_URL'])
    logger_stage.info(f'{response}')

    # Build schedule
    stage_schedule_csv = json.loads(response)['schedule_csv']
    stage_schedule = loadshedding_thingamabob.schedule.Schedule.from_string(
        stage_schedule_csv)
    logger.info(f'stage_schedule: {stage_schedule}')

    # Get current stage
    date_now = datetime.now()
    date_soon = date_now + timedelta(minutes=configuration_user['PAD_START'])
    stage_current = stage_schedule.stage(date_soon.timestamp())
    logger.info(f'stage_current: {stage_current}')
    # stage_current = stage_schedule

    transforms = {
        'stage': lambda x: int(x)
    }
    sched = lutils.lcsv.read_csv(configuration_user['SCHEDULE_CSV'],
                                 transforms=transforms,
                                 delimiter=';')

    shedding = check_shedding(
        stage_current, sched,
        configuration_user, configuration_system,
        date_now
        )

    if not shedding:
        logger.info('status: not shedding any loads')
        return False

    if configuration_user['GUI_NOTIFICATION']:
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


def check_row(row, date_now, tomorrow, configuration_user):
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
    if (start - configuration_user['PAD_START']
            <= now <=
            end - configuration_user['IGNORE_END']):
        # We're shedding now
        return True

    return False


def check_shedding(
        curr_stage, sched, configuration_user, configuration_system, date_now):
    day = str(date_now.day)
    date_tomorrow = date_now + timedelta(days=1)
    day_tomorrow = str(date_tomorrow.day)

    for row in sched:
        if not row['stage'] <= curr_stage:
            continue

        if (row[day] == str(configuration_user['AREA']) and
                check_row(row, date_now, False, configuration_user)):
            return True

        if (row[day_tomorrow] == str(configuration_user['AREA'])
                and check_row(row, date_now, True, configuration_user)):
            return True

    return False


def get_stage_schedule(api_url: str, attempts=20):
    # We'll try x times
    for x in range(attempts):
        try:
            response = urllib.request.urlopen(api_url, timeout=10)
            response = response.read().decode()

            return response
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
    def switch_last_two_suffixes(base_filename: str):
        """Switch the last two suffixes of the filename
        Used in TimedRotatingFileHandler as .namer
            to switch fix the filename upon rotating, e.g.
            filename = module.log
            on rotate: base_filename = module.log.datetime

        Output of this function will then be:
            switch_last_two_suffixes("module.log.datetime") -> module.datetime.log

        Args:
            base_filename (str): _description_

        Returns:
            _type_: _description_
        """
        base_filename = pathlib.PurePath(base_filename)
        parent = base_filename.parent
        name = base_filename.name.split('.')
        assert len(name) >= 2

        name = '.'.join(name[:-2] + [name[-1], name[-2]])

        return str(parent / name)

    def get_logger(name, filename):
        filename = pathlib.Path(filename)
        if not filename.suffix:
            filename = filename.with_suffix('.log')

        logger_crash = logging.getLogger(name)
        logger_crash.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        logger_crash.addHandler(ch)
        fh = logging.handlers.TimedRotatingFileHandler(
            filename, when="midnight"
            )
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
    except configuration.VersionError as e:
        message = str(e)
        logger.critical(message)
        logger_crash.critical(message)
        exit()

    main(configuration_system, configuration_user, logger, logger_stage)
