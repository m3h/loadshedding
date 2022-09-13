#!/usr/bin/env python3
import logging
import logging.handlers
from datetime import datetime, timedelta
import os
import urllib.request
import json
import pathlib


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

    date_now = datetime.now()

    if configuration_user['QUERY_MODE'].lower() == 'direct':
        stage_current = get_stage_direct(configuration_user['API_URL'])
    elif configuration_user['QUERY_MODE'].lower() == \
            'loadshedding_thingamabob':
        response = get_stage_schedule(configuration_user['API_URL'])
        logger_stage.info(f'{response}')

        # Build schedule
        import loadshedding_thingamabob.schedule
        stage_schedule_csv = json.loads(response)['schedule_csv']
        stage_schedule = \
            loadshedding_thingamabob.schedule.Schedule.from_string(
                stage_schedule_csv
            )
        logger.info(f'stage_schedule: {stage_schedule}')

        # Get current stage
        date_soon = \
            date_now + timedelta(minutes=configuration_user['PAD_START'])
        stage_current = stage_schedule.stage(date_soon.timestamp())
    logger.info(f'stage_current: {stage_current}')

    transforms = {
        'stage': lambda x: int(x)
    }
    schedule = lutils.lcsv.read_csv(configuration_user['SCHEDULE_CSV'],
                                    transforms=transforms,
                                    delimiter=';')

    shedding = check_shedding(
        stage_current, schedule,
        configuration_user,
        date_now
    )

    if not shedding:
        try:
            if (configuration_user['RAN_CHECK']):
                if os.path.exists(configuration_system['LOGRAN']):
                    os.remove(configuration_system['LOGRAN'])
        except Exception as e:
            logger.exception(e)
        logger.info('status: not shedding any loads')
        return False

    # Override RAN Check
    # In a very lenient try-except block, if fails it shouldn't block the
    #   expected behaviour (e.g. running the command)
    override_ran = False
    try:
        if (configuration_user['RAN_CHECK']):
            if os.path.exists(configuration_system['LOGRAN']):
                with open(configuration_system['LOGRAN'], 'r') as f:
                    area_ran, datetime_ran, stage_ran = \
                        f.read().strip().split(';')
                area_ran = str(area_ran)
                datetime_ran = datetime.fromisoformat(datetime_ran)
                stage_ran = int(stage_ran)

                blocks_ran = set(blocks_shedding(
                    stage_ran, schedule,
                    configuration_user,
                    datetime_ran
                ))
                blocks_current = set(blocks_shedding(
                    stage_current, schedule,
                    configuration_user,
                    date_now
                ))

                # Dont run the loadshedding command if:
                # (1) the area is the same and
                # (2) there is some overlap between the blocks for which the
                #   command previously ran and the current triggered blocks
                # (3) And the difference between the previous trigger and this
                #   trigger is less than a day. This handles cases where the
                #   device is only turned on on the same day of the following
                #   month and it is still loadshedding
                if (area_ran == str(configuration_user['AREA']) and
                            blocks_ran.intersection(blocks_current) and
                            (date_now - datetime_ran < timedelta(days=1))
                        ):
                    override_ran = True

            if not override_ran:
                with open(configuration_system['LOGRAN'], 'w') as f:
                    f.write(
                        f'{configuration_user["AREA"]}'
                        f';{date_now.isoformat()}'
                        f';{stage_current}'
                    )
    except Exception as e:
        logger.exception(e)

    if override_ran:
        message = f'Cancelled by override ran check ({datetime_ran})'
        logger.info(message)
        return

    # No overrides, just run the command
    message = 'Executing loadshedding cmd "{}"'.format(
        configuration_user['CMD'])
    logger.info(message)

    if configuration_user['GUI_NOTIFICATION']:
        override_gui, reason = get_override_status(
            configuration_system['NOTIFICATION_TIMEOUT'],
            "Loadshedding imminent!")
    else:
        override_gui, reason = False, None

    if override_gui:
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


def iterate_shedding_blocks(
        stage_current, schedule, configuration_user, date_check):
    day = str(date_check.day)
    date_tomorrow = date_check + timedelta(days=1)
    day_tomorrow = str(date_tomorrow.day)

    for i, row in enumerate(schedule):
        if not row['stage'] <= stage_current:
            continue

        if (row[day] == str(configuration_user['AREA']) and
                check_row(row, date_check, False, configuration_user)):
            yield i, row['start'], row['end'], row['stage'], row[day]

        if (row[day_tomorrow] == str(configuration_user['AREA'])
                and check_row(row, date_check, True, configuration_user)):
            yield i, row['start'], row['end'], row['stage'], row[day_tomorrow]


def check_shedding(
        stage_current, schedule, configuration_user, date_check):
    return any(iterate_shedding_blocks(
        stage_current, schedule, configuration_user, date_check
    ))


def blocks_shedding(
        stage_current, schedule, configuration_user, date_check):
    return list(iterate_shedding_blocks(
        stage_current, schedule, configuration_user, date_check
    ))


def get_stage_direct(api_url: str, attempts=20):
    # We'll try x times
    for x in range(attempts):
        try:
            req = urllib.request.urlopen(api_url, timeout=10)
            stage_str = req.read().decode()
            stage = int(stage_str) - 1  # The API has +1

            logger_stage.info(f'{stage}')

            return stage
        except Exception as e:
            logger.warning(str(e))
    logger.error('Failure calling API, after {} attempts'.format(attempts))
    exit()


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
            switch_last_two_suffixes("module.log.datetime") ->
            module.datetime.log

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
        import argparse

        parser = argparse.ArgumentParser(
            description='Automatic hibernate during loadshedding'
        )
        parser.add_argument(
            '--configuration_system', type=str,
            default='configuration_system.yaml',
            help='Path to the system configuration file.'
        )
        parser.add_argument(
            '--configuration_user', type=str,
            default='configuration_user.yaml',
            help='Path to the user configuration file.'
        )
        args = parser.parse_args()
    except Exception as e:
        logger_crash.exception(e)
        exit()

    try:
        configuration_system = configuration.read_configuration_system(
            args.configuration_system)
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
            args.configuration_user)
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
