"""Module to test read_file.py functions"""
# stdlib
import os

# third party
import pandas as pd

# relative
from tmh_server import read_file as rf

TEST_DIR: str = "test"
TEST_FILE_CSV: str = "test_data.csv"
TEST_FILE_CONFIG: str = "test_config.json"


def test_file_exists():
    assert rf.file_exists(os.path.join(os.getcwd(), TEST_DIR, TEST_FILE_CSV))


def test_csv_to_pd():
    """
    TEST_FILE has the following structure
    ,Humidity,VOC,NO2
    0,82.46,155,59.17
    1,82.42,169,54.83
    2,82.4,191,54.72
    3,82.4,188,53.84
    """
    df: pd.DataFrame = rf.csv_to_pd(os.path.join(os.getcwd(), TEST_DIR),
                                    TEST_FILE_CSV)
    assert isinstance(df, pd.DataFrame)
    assert {"Humidity", "VOC", "NO2"} == set(df.columns)
    assert df.shape[0] == 130


def test_json_to_dict():
    """
    """
    config: dict = rf.json_to_dict(os.path.join(os.getcwd(), TEST_DIR),
                                   TEST_FILE_CONFIG)
    assert isinstance(config, dict)
    assert all([item in ["fl_params", "training_params"] for item in config.keys()])
    assert all([item in ["server_address", "fl"] for item in config["fl_params"].keys()])
    assert all([item in ["data", "model", "python_exec"] for item in config["training_params"].keys()])
