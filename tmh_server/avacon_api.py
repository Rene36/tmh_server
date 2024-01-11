"""Module for GET requests on Avacon API"""
# stdlib
import io
import time
import logging
from datetime import datetime, timedelta

# third party
import pandas as pd
from requests import Session, Request, Response

# relative
from tmh_server import read_file


class AvaconAPI:
    """
    Functions to work with the Avacon API.
    """
    def __init__(self,
                 config_path: str,
                 config_name: str) -> None:
        # Config variables
        self.config_path: str = config_path
        self.config_name: str = config_name
        self.config: dict = {}
        self.config_keys: list = ["networkoperator", "type", "chunkNr",
                                  "param1", "op1", "startOp", "val1",
                                  "param2", "op2", "endOp", "val2"]
        self.loop_counter: int = 0

        # Request variables
        self.request: Request = None
        self.response: Response = None
        self.content: pd.DataFrame = pd.DataFrame()

    def call_api(self) -> pd.DataFrame:
        """
        Call Avacon API based on a config file and process the response.
        """
        start: int = time.time()
        if self._validate_config():
            while self._data_missing():
                self._build_request()
                self._run_request()
                self._extract_content()
                self._start_to_datetime()
            print(f"API calls took {time.time() - start}s")
            return self.content
        else:
            print("failed")

    def _validate_config(self) -> bool:
        self.config: dict = read_file.json_to_dict(self.config_path,
                                                   self.config_name)
        if all(e in list(self.config.keys()) for e in self.config_keys):
            return True
        return False

    def _build_request(self,
                       data_type: str="csv",) -> str:
        """
        
        Example API call:
        https://redispatch-run.azurewebsites.net/api/export/csv?&networkoperator=ava&type=finished&chunkNr=1&param1=start&op1=gOE&startOp=ge&val1=2020-01-01&param2=end&op2=lOE&endOp=le&val2=2020-03-31
        """
        available_types: list = ["csv", "xlsx", "pdf"]
        if data_type in available_types:
            url: str = f"https://redispatch-run.azurewebsites.net/api/export/{data_type}"
        else:
            logging.error("%s not in %s", data_type, available_types)
            raise Exception(f"{data_type} not in {available_types}")

        self.request: Request = Request("GET",
                                        url=url,
                                        params=self.config).prepare()

    def _run_request(self):
        s: Session = Session()
        self.response: Response = s.send(self.request)
        if self.response.status_code == 200:
            logging.info("API request response is %s", self.response.status_code)
        elif self.response.status_code == 405:
            logging.error("API request response is 405")
            raise Exception(f"API request response is {self.response.status_code}")
        return self.response

    def _extract_content(self) -> pd.DataFrame:
        df: pd.DataFrame = pd.read_csv(io.StringIO(self.response.content.decode("utf-8")),
                                       sep=";")
        df.columns = df.columns.str.replace('"', "")
        if self.content.empty:
            self.content = df
        else:
            self.content = pd.concat([self.content, df], ignore_index=True, sort=False)
            print(f"Extracted {self.content.shape} data points from API")

    def _start_to_datetime(self):
        if "Start" in self.content.columns:
            self.content["Start"] = pd.to_datetime(self.content["Start"],
                                                   format="%Y-%m-%d %H:%M:%S")
            self.content.sort_values(by=["Start"],
                                     ascending=True,
                                     inplace=True)
            self.content.reset_index(drop=True,
                                     inplace=True)
        else:
            logging.error("Start not in data frame columns %s", self.content.columns)
            raise KeyError(f"Start not in data frame columns {self.content.columns}")

    def _data_missing(self) -> bool:
        self.loop_counter += 1
        if self.content.empty:
            return True
        if self.content.iloc[-1]["Start"] <= datetime.strptime(self.config["val2"], "%Y-%m-%d") - timedelta(days=1) and self.loop_counter <= 4:
            self.config["val1"] = self.content.iloc[-1]["Start"].strftime("%Y-%m-%d")
            return True
        return False
