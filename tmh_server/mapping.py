"""Module to generate mapping from EEG Anlagenschlüssel to nominal power"""
# stdlib
import os
import logging

# third party
import pandas as pd


class Mapping:
    """
    Get and map IDs from different data sources to extract
    the nominal power for a given plant ID.
    """
    def __init__(self,
                 path_anlagenstammdaten: str,
                 file_bewegungsdaten: str) -> None:
        self.path_anlagenstammdaten: str = path_anlagenstammdaten
        self.file_bewegungsdaten: str = file_bewegungsdaten

        self.mapping_id_to_power: dict = {}
        self.df_db: pd.DataFrame = pd.DataFrame()
        self.df_mastr: pd.DataFrame = pd.DataFrame()

    def set_df(self,
               df: pd.DataFrame) -> None:
        """
        Setter for internal variable
        :param df: pandas dataframe, data to write to database
        """
        self.df_db: pd.DataFrame = df

    def get_nb_mastr_nrs(self) -> list:
        """
        Get Marktstammdaten numbers of network operators for scrapping
        the installed power plants in their balance zone.

        :return list, 
        """
        if os.path.isfile(os.path.join(self.path_anlagenstammdaten,
                                       self.file_bewegungsdaten)):
            df: pd.DataFrame = pd.read_csv(os.path.join(self.path_anlagenstammdaten,
                                                        self.file_bewegungsdaten),
                                           encoding="iso-8859-1",
                                           sep=";")
            if "NB_Mastr_Nr" in df.columns:
                nb_mastr_nr: list = list(df["NB_Mastr_Nr"].unique())
                return nb_mastr_nr
            logging.error("Column NB_Mastr_Nr not in dataframe")
            raise KeyError()

        if os.path.isfile(os.path.join(self.path_anlagenstammdaten, "nb_mastr_nr.csv")):
            nb_mastr_nr: pd.DataFrame = pd.read_csv(os.path.join(self.path_anlagenstammdaten,
                                                                 "nb_mastr_nr.csv"))
            nb_mastr_nr: list = nb_mastr_nr[0].values.tolist()
            return nb_mastr_nr

        logging.error("No information about EEG Anlagen / plant_ids")
        raise OSError()

    def get_merged_snbs(self):
        """
        Read merged data from all SNBs.
        """
        self.df_mastr: pd.DataFrame = pd.read_csv(os.path.join(self.path_anlagenstammdaten,
                                                               "mastr_2022_simplified.csv"),
                                                  sep=";",
                                                  usecols=["EEG-Anlagenschlüssel",
                                                           "Nettonennleistung der Einheit"])

    def create_mapping(self) -> dict:
        """

        :return dict, mapping of power plant ID to nominal power
        """
        if "EEG-Anlagenschlüssel" in self.df_mastr.columns:
            self.df_mastr.dropna(subset=["EEG-Anlagenschlüssel"], inplace=True)
            self.df_mastr.set_index("EEG-Anlagenschlüssel", inplace=True)
            self.mapping_id_to_power: dict = self.df_mastr["Nettonennleistung der Einheit"].to_dict()
        else:
            logging.error("Column EEG-Anlagenschlüssel not in dataframe")
            raise KeyError("Column EEG-Anlagenschlüssel not in dataframe")

    def map_power_to_plant_id(self):
        """
        Map power plant IDs to their nominal power.
        """
        if "power_nominal" in self.df_db.columns and "plant_id" in self.df_db.columns:
            self.df_db["power_nominal"] = self.df_db["plant_id"].map(self.mapping_id_to_power)
            self.df_db.dropna(subset=["power_nominal"], inplace=True)
            self.df_db["power_nominal"] = self.df_db["power_nominal"].str.replace(",", ".").astype(float)
        else:
            logging.error("Columns not in dataframe")
            raise KeyError("Columns not in dataframe")

    def calculate_curtailed_power(self):
        """
        Calculate curtailed power in kW.
        """
        self.df_db["power_curtailed"] = self.df_db["power_nominal"] * (100 - self.df_db["level"]) / 100

    def calculate_curtailed_energy(self):
        """
        Calculate curtailed energy in kWh.
        """
        self.df_db["energy_curtailed"] = self.df_db["power_curtailed"] * self.df_db["duration"] / 60
