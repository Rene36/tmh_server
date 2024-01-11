"""Module to read date from files."""
# stdlib
import os
import json
import logging

# third party
import pandas as pd


def file_exists(full_path: str) -> bool:
    """
    Checks if a file in a given directory exists.

    :param full_path: string, | full path of folder where file is stored
                              | with suffix e.g. .csv, .json
    :return: boolean, result if file existing check
    """
    return os.path.isfile(full_path)


def csv_to_pd(path: str,
              file_name: str,
              separator: str=",",
              decimal: str=".",
              low_memory: bool=True) -> pd.DataFrame:
    """
    Read in a .csv file. Save the data in a pandas data frame if
    the file exists and a matching encoding is found.
    For more Python build-in encodings check:
    https://docs.python.org/2/library/codecs.html#standard-encodings

    :param path: string, path of folder where .csv file is saved
    :param file_name: string, | name of .csv file. Has to have
                              | the extension .csv in the variable
    :param skip_rows: int, | number of rows which are
                           | ignored in the import
    :param separator: string, column separator
    :param decimal: string, decimal separator
    :param low_memory: bool, to ensure no mixed types either set False
    :return: pandas data frame, data from .csv file
    """
    encodings: list = ["utf-8", "utf-16", "utf-32",
                       "latin1", "ascii",
                       "iso-8859-1", "iso8859_2", "iso8859_15",
                       "cp037", "cp437", "cp500",
                       "cp850", "cp852", "cp858",
                       "mac_latin2", "mac_roman"]

    full_path: str = os.path.join(path, file_name)

    if file_exists(full_path):
        for encoding in encodings:
            try:
                data: pd.DataFrame = pd.read_csv(full_path,
                                                 sep=separator,
                                                 decimal=decimal,
                                                 encoding=encoding,
                                                 low_memory=low_memory
                                                 )
                return data

            except (UnicodeDecodeError, LookupError):
                continue

    logging.warning("%s not found", full_path)
    raise OSError(f"{full_path} not found")


def json_to_dict(path: str,
                 file_name: str) -> dict:
    """
    Read in a .json file and save the data in a dictionary if
    the file exists.

    :param path: string, path of folder where .json file is saved
    :param file_name: string, | name of .json file. Has to have
                              | the extension .json in the variable
    :return: dict data frame, data from .json file
    """
    full_path: str = os.path.join(path, file_name)

    if file_exists(full_path):
        with open(full_path, encoding="utf-8") as json_file:
            data: dict = json.load(json_file)
        return data

    logging.warning("%s not found", full_path)
    raise OSError(f"{full_path} not found")
