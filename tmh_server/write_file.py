"""
Module providing functions to write data to a file.
"""
# stdlib
import os

# third party
import pandas as pd


def file_exists(full_path: str) -> bool:
    """
    Check if the file already exists.

    :param full_path: string, | full path of folder where file is stored
                              | with suffix e.g. .csv, .json
    :return: boolean, True if file exists else False
    """
    return os.path.isfile(full_path)


def pd_to_csv(data: pd.DataFrame,
              path: str,
              file_name: str,
              separator=",",
              index=False,
              encoding="utf-8",
              overwrite=False) -> None:
    """
    Writes a pandas data frame to a .csv file.

    :param data: pandas data frame, data which is written to a .csv file
    :param path: string, path of folder where .csv file is written to
    :param file_name: string, name of .csv file
    :param separator: string, column separator
    :param decimal: string, decimal separator
    :param index: boolean, | print index of pandas data frame in .csv
                           | file or not
    :param encoding: string, | type of encoding, e.g. "ANSI", "utf-8",
                             | "utf-16", "latin1", "ascii", "iso-8859-1"
    :param header: boolean, print header in .csv file or not
    :param overwrite: boolean, | True if an already existing file can
                               | be overwritten
    """
    full_path: str = os.path.join(path, file_name)

    if not overwrite and file_exists(full_path):
        print("No file written for " + full_path +
              "\tThe file already exists and overwriting is "
              "disabled.")
    else:
        data.to_csv(full_path,
                    sep=separator,
                    index=index,
                    encoding=encoding
                    )
