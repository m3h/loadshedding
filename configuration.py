"""
Simply library to
    (i)     read YAML configuration files
    (ii)    check their validity
"""
import yaml


class MissingKeyError(LookupError):
    pass


class VersionError(RuntimeError):
    pass


def read_configuration(path: str):
    """Reads the YAML configuration file at path and converts all keys to uppercase

    Args:
        path (str): Path to YAML configuration file

    Returns:
        [dict]: Configuration dictionary
    """
    with open(path, 'r') as f:
        configuration = yaml.safe_load(f)
    configuration = {k.upper(): v for k, v in configuration.items()}

    return configuration


def read_configuration_and_check(
        path: str, keys: list, configuration_file_type, version: str):
    """Reads the YAML configuration file at path and
    check that all all keys are present in the configuration file

    Args:
        path (str): Path to YAML configuration file
        keys (list): List of keys that must be present
        configuration_file_type (str): Type of configuration file read
        version (str): Expected version

    Raises:
        FileNotFoundError: Raised when the file at path does not exist
        MissingKeyError: Raised when one or more keys are not present in the
            configuration file

    Returns:
        [dict]: Configuration dictionary
    """
    def version_split(version: str):
        return tuple(int(x) for x in version.split('.'))

    configuration = read_configuration(path)

    for key in keys:
        if 'VERSION' not in configuration:
            raise VersionError('VERSION not specified in configuration file')
        if version_split(configuration['VERSION']) < version_split(version):
            raise VersionError(
                'VERSION mismatch. '
                f'Expected: {version} - Specified: {configuration["VERSION"]}'
            )
        if key not in configuration:
            raise MissingKeyError(
                f'{key} not in {configuration_file_type} '
                'configuration file "{path}"')

    return configuration


def read_configuration_system(path):
    """Reads and validates a system configuration file

    Args:
        path (str): Path to YAML configuration file

    Raises:
        FileNotFoundError: Raised when the file at path does not exist
        MissingKeyError: Raised when one or more keys are not present in the
            configuration file

    Returns:
        [dict]: System configuration dictionary
    """
    keys = ['LOGSTAGE', 'LOG', 'NOTIFICATION_TIMEOUT']
    version = '0.2.1'
    return read_configuration_and_check(path, keys, 'system', version)


def read_configuration_user(path):
    """Reads and validates a user configuration file

    Args:
        path (str): Path to YAML configuration file

    Raises:
        FileNotFoundError: Raised when the file at path does not exist
        MissingKeyError: Raised when one or more keys are not present in the
            configuration file

    Returns:
        [dict]: System configuration dictionary
    """
    keys = [
        'API_URL', 'AREA', 'QUERY_MODE', 'CMD',
        'SCHEDULE_CSV', 'PAD_START', 'IGNORE_END',
        'RAN_CHECK',
    ]
    version = '0.2.2'
    return read_configuration_and_check(path, keys, 'user', version)
