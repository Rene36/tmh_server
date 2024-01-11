"""Module to test write_file.py functions"""
# stdlib
import os

# third party
import pandas as pd

# relative
from tmh_server import write_file as wf

TEST_DIR: str = "test"
TEST_FILE_CSV: str = "test_data.csv"
TEST_FILE_CSV_WRITE: str = "test_data_write.csv"


def test_file_exists():
    assert wf.file_exists(os.path.join(os.getcwd(), TEST_DIR, TEST_FILE_CSV))


def test_pd_to_csv():
    wf.pd_to_csv(path=os.path.join(os.getcwd(), TEST_DIR),
                 file_name=TEST_FILE_CSV_WRITE,
                 data=pd.DataFrame({"col1": [1, 2, 3],
                                    "col2": [4, 5, 6]}))
    assert wf.file_exists(os.path.join(os.getcwd(), TEST_DIR, TEST_FILE_CSV_WRITE))
    os.remove(os.path.join(os.getcwd(), TEST_DIR, TEST_FILE_CSV_WRITE))
