"""Module to scrap the Marktstammdatenregister"""
# stdlib
import os
import time
import logging
from collections import namedtuple
from urllib.parse import urlunparse

# third party
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


class MastrScrapper:
    """
    Build URL and then downlaod information from Marktstammdatenregister
    """
    def __init__(self) -> None:
        self.nb_mastr_nr: list = None
        self.url: str = None
        self.path_download: str = os.path.join(os.environ["HOME"],
                                               "Downloads")

    def set_nb_mastr_nr(self,
                        nb_mastr_nr: str):
        """
        Set internal variable
        :param nb_mastr_nr: str, ID of network operator
        """
        self.nb_mastr_nr = nb_mastr_nr

    def _build_url(self) -> str:
        """
        
        :return: url, str URL string
        """
        components = namedtuple(
            typename="Components",
            field_names=["scheme", "netloc", "params", "path", "query", "fragment"]
        )
        url: str = urlunparse(components(
            scheme="https",
            netloc="www.marktstammdatenregister.de",
            path="/MaStR/Einheit/Einheiten/ErweiterteOeffentlicheEinheitenuebersicht",
            params="",
            query=f"filter=Inbetriebnahmedatum%20der%20EEG-Anlage~lt~%2701.01.2023%27~and~MaStR-Nr.%20des%20Anschluss-Netzbetreibers~ct~%27{self.nb_mastr_nr}%27",
            fragment="",
        ))
        self.url: str = url.replace("/;", "")

    def _remove_existing_stromerzeuger_files(self):
        """
        Remove any files having a similar name as the one
        to download.
        """
        if os.path.isfile(self.path_download):
            os.remove(os.path.join(self.path_download,
                                   "Stromerzeuger.csv"))

    def download_via_link(self) -> None:
        """
        
        :param nb_mastr_nr: str, ID of network operator
        """
        self._remove_existing_stromerzeuger_files()
        self._build_url()

        driver = webdriver.Firefox()
        driver.get(self.url)
        time.sleep(3)

        try:
            driver.find_element(By.CSS_SELECTOR,
                                "#grid-stromerzeugung-erweitert .gridReloadBtn").click()
            time.sleep(5)
            driver.find_element(By.CSS_SELECTOR,
                                "#stromerzeugung .panel-heading .dropdown > .btn").click()
            time.sleep(.5)
            driver.find_element(By.CSS_SELECTOR,
                                "#ui-id-2").click()
            time.sleep(.5)
            value_field = driver.find_element(By.CSS_SELECTOR,
                                            "#countEinheit")
            value_field: str = value_field.text.replace(".", "")
            if int(value_field) <= 20000:
                driver.find_element(By.CSS_SELECTOR,
                                    "#jsFunctionButton > .labeltext").click()
                while "Stromerzeuger.csv" not in os.listdir(self.path_download):
                    time.sleep(1)
            else:
                print(f"Skip {self.nb_mastr_nr} because of too many entries {int(value_field)}")
                driver.find_element(By.CSS_SELECTOR,
                                    "#cancelButton").click()
        except NoSuchElementException:
            logging.warning("No entries exist for %s", self.nb_mastr_nr)
        driver.close()

    def move_downloaded_file(self):
        """
        Move file from download directory to project directory.
        """
        full_path: str = os.path.join(self.path_download,
                                      "Stromerzeuger.csv")
        if os.path.isfile(full_path):
            os.rename(full_path,
                      os.path.join(os.getcwd(),
                                   "anlagenstammdaten", "SNBs",
                                   self.nb_mastr_nr + ".csv"))

    def merge_snbs_into_one_csv(self,
                                path_anlagenstammdaten: str) -> None:
        """
        Combines all individual SNB data set scrapped from Marktstammdatenregister
        into one CSV

        :param path_anlagenstammdaten: str, 
        """
        snbs_path: str = os.path.join(path_anlagenstammdaten, "SNBs")
        df: pd.DataFrame = pd.DataFrame()
        for snb in [i for i in os.listdir(snbs_path) if ".csv" in i]:
            df_snb: pd.DataFrame = pd.read_csv(os.path.join(snbs_path, snb),
                                               sep=";")
            df: pd.DataFrame = pd.concat([df, df_snb],
                                         ignore_index=True,
                                         sort=False)
            if "Inbetriebnahmedatum der Einheit" in df.columns:
                df["Inbetriebnahmedatum der Einheit"] = pd.to_datetime(df["Inbetriebnahmedatum der Einheit"],
                                                                       format="%d/%M/%Y")
                df = df[df["Inbetriebnahmedatum der Einheit"] <= "2023-01-01"]
                df.to_csv(os.path.join(path_anlagenstammdaten, "mastr_2022.csv"),
                          sep=";")
            else:
                logging.error("Column Inbetriebnahmedatum der Einheit not in dataframe")
                raise KeyError()
