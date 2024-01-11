"""Module to test process_data.py functions"""

# third party
import pandas as pd

# relative
from tmh_server.process_data import ProcessData

DF: pd.DataFrame = pd.DataFrame(data={"ID": [1, 1, 3, 6],
                                      "Einsatz-ID": ["AVA1", "AVA2", "AVA3", "AVA4"],
                                      "Start": ["2020-01-01 10:00:00", "2020-01-02 10:00:00", "2020-01-03 10:00:00", "2020-01-04 10:00:00"],
                                      "Ende": ["2020-01-01 10:05:00", "2020-01-02 10:05:00", "2020-01-03 10:05:00", "2020-01-04 10:05:00"],
                                      "Dauer (Min)": [5, 5, 5, 5],
                                      "Stufe (%)": [0, 30, 60, 89],
                                      "Ursache": ["a", "b", "c", "d"],
                                      "Anlagenschlüssel": ["E123", "E456", "E789", "E135"],
                                      "Netzbetreiber": ["Avacon", "Avacon", "Avacon", "Avacon"]})
TEST_OBJECT: ProcessData = ProcessData(DF)


def test_get_data():
    df: pd.DataFrame = TEST_OBJECT.get_data()
    assert isinstance(df, pd.DataFrame)
    assert all(e in list(df.columns) for e in DF.columns)


def test_clean():
    TEST_OBJECT.clean()
    df: pd.DataFrame = TEST_OBJECT.get_data()
    assert all(e in ["start_curtailment", "end_curtailment",
                     "duration", "level", "cause", "plant_id",
                     "operator"] for e in df.columns)
    assert df.shape[0] == 2
    assert df["level"].isin([0, 30, 60]).all()
