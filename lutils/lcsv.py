#!/usr/bin/env python3
"""
Implements the csv-dict reading of the schedules
"""
import csv


def read_csv(filepath: str, transforms: dict = {}, delimiter: str = ';'):
    """Read csv schedules, and returns a list of dicts with the contents

    Args:
        filepath (str): Path to the schedule csv
        delimiter (str): The delimiter for the csv
        transforms (dict): A dict of transform tuples to apply to the data, in
        the form of {'heading': fn} where 'heading' corresponds to the
        heading in the title, and fn is a function that receives a str and
        applies a transformation to the given item in the csv.

    Returns:
        [list(dict)]: List of dicts, where each item in the list corresponds to
        a row in the CSV, and each key is a header in the CSV.
    """

    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter)

        data = list(reader)
        for row in data:
            for k in transforms:
                row[k] = transforms[k](row[k])
        return data
