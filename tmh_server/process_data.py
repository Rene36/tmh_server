"""Module to change a pandas dataframe"""
# stdlib
import time
import logging
from typing import Union

# third party
import pandas as pd


class ProcessData:
    """
    Functions to clean and pre-process a given
    pandas dataframe for further usage.
    """
    def __init__(self,
                 df: pd.DataFrame) -> None:
        self.df: pd.DataFrame = df

    def clean(self):
        """
        Summary of internal functions to pre-process a pandas dataframe
        """
        start: int = time.time()
        self._remove_duplicates(col_name="ID")
        self._drop_unnecessary_columns()
        self._rename_columns()
        self._remove_wrong_levels()
        self._remove_wrong_causes()
        self._remove_wrong_plant_ids()
        self._col_to_datetime(col_name=["start_curtailment",
                                        "end_curtailment"])
        self._sort_by_column(col_name="start_curtailment")
        self._validate_duration()
        print(f"Data processing took {time.time() - start}")

    def get_data(self) -> pd.DataFrame:
        """
        Getter fucntion return pandas dataframe class object

        :return: pandas dataframe,
        """
        return self.df

    def _remove_duplicates(self,
                           col_name: str):
        if col_name in self.df.columns:
            self.df.drop_duplicates(subset=col_name, inplace=True)
        else:
            logging.error("Column %s not in dataframe", col_name)
            raise KeyError(f"Column {col_name} not in dataframe")

    def _drop_unnecessary_columns(self):
        self.df.drop(["ID", "Einsatz-ID", "Gebiet",
                      "Ort Engpass", "Anforderer", "Anlagen-ID",
                      "Abrechnungs-ID", "Entschädigungspflicht"],
                      errors="ignore",
                      axis=1,
                      inplace=True)

    def _rename_columns(self):
        self.df.rename(columns={"Start": "start_curtailment",
                                "Ende": "end_curtailment",
                                "Dauer (Min)": "duration",
                                "Stufe (%)": "level",
                                "Ursache": "cause",
                                "Anlagenschlüssel": "plant_id",
                                "Netzbetreiber": "operator"},
                        errors="raise",
                        inplace=True)

    def _remove_wrong_levels(self):
        if "level" in self.df.columns:
            self.df = self.df[self.df["level"].isin([0, 30, 60])]
        else:
            logging.error("Column level not in dataframe")
            raise KeyError("Column level not in dataframe")

    def _remove_wrong_causes(self):
        if "cause" in self.df.columns:
            self.df = self.df[self.df["cause"] != "Test"]
        else:
            logging.error("Column cause not in dataframe")
            raise KeyError("Column cause not in dataframe")

    def _remove_wrong_plant_ids(self):
        if "plant_id" in self.df.columns:
            self.df = self.df[self.df["plant_id"] != "Siehe Veröffentl. Netzbetreiber!"]
        else:
            logging.error("Column plant_id not in dataframe")
            raise KeyError("Column plant_id not in dataframe")

    def _col_to_datetime(self,
                         col_name: Union[str, list],
                         timestamp_format: str="%Y-%m-%d %H:%M:%S"):
        if isinstance(col_name, str) and col_name in self.df.columns:
            self.df[col_name] = pd.to_datetime(self.df[col_name],
                                               format=timestamp_format)
        elif all(e in list(self.df.columns) for e in col_name):
            for c in col_name:
                self.df[c] = pd.to_datetime(self.df[c],
                                            format=timestamp_format)
        else:
            logging.error("Column %s not in dataframe", col_name)
            raise KeyError(f"Column {col_name} not in dataframe")

    def _sort_by_column(self,
                        col_name: str):
        if col_name in self.df.columns:
            self.df.sort_values(by=col_name, ascending=True, inplace=True)
        else:
            logging.error("Column %s not in dataframe", col_name)
            raise KeyError(f"Column {col_name} not in dataframe")

    def _validate_duration(self):
        self.df["duration"] = (self.df["end_curtailment"] - self.df["start_curtailment"]).dt.total_seconds() / 60
        self.df["duration"] = self.df["duration"].round(0).astype(int)
