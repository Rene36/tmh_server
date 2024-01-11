"""Module to work with a PostgreSQL database"""
# stdlib
import sys
import time
import logging
from io import StringIO

# relative
from tmh_server import read_file

# third party
import psycopg2
import pandas as pd
from psycopg2 import sql


class PostgreSQL:
    """
    Allows to interact with a PostgreSQL database by getting
    or retrieving information.

    Default port = 5432.
    Run SELECT * FROM pg_settings WHERE name = 'port'; in command line to
    see the specified port.
    """

    def __init__(self,
                 config_path: str,
                 config_name: str,
                 data: pd.DataFrame):
        self.df: pd.DataFrame = data

        # Config variables
        self.config_path: str = config_path
        self.config_name: str = config_name 
        self.config: dict = {}
        self.config_keys: list = ["user", "password",
                                  "db_name", "table_name"]

        self.connection = None
        self.cur = None

    def set_df(self,
               df: pd.DataFrame) -> None:
        """
        Setter for internal variable
        :param df: pandas data frame, data to write to database
        """
        self.df = df

    def connect_and_insert(self):
        """
        Insert data based on config file into an existing table.
        """
        self.connect_to_db()
        if self.config["table_name"] in self._get_tables():
            self._insert_in_table_copy()
            self.close_connection()

    def _validate_config(self) -> bool:
        self.config: dict = read_file.json_to_dict(self.config_path,
                                                   self.config_name)
        if all(e in list(self.config.keys()) for e in self.config_keys):
            return True
        return False

    def connect_to_db(self,
                      host: str="localhost",
                      port: int=5432):
        """
        Connects to a PostgreSQL database if a db_name is given.

        :param host; str, IP address of PostgreSQL server
        :param port: int, port of PostgreSQL server
        :param user: str, PostgreSQL user name
        :param password: str, password for user
        :param db_name: str, database name
        """
        try:
            if self._validate_config():
                conn_string = "host=" + host + \
                            " port=" + str(port) + \
                            " user=" + self.config["user"] + \
                            " password=" + self.config["password"]
                if self.config["db_name"] is not None:
                    conn_string += " dbname=" + self.config["db_name"]

                self.connection = psycopg2.connect(conn_string)
                self.cur = self.connection.cursor()
            else:
                raise Exception()

        except psycopg2.OperationalError as e:
            logging.error(e)

    def _get_tables(self,
                    public=True) -> list:
        """
        Returns all tables from the connect Postgresql host depending
        on the access of the table (public or not).

        :param public: boolean, list just public or all available tables
        :return: list, available tables
        """
        if public:
            self.cur.execute("""SELECT table_name FROM
            information_schema.tables WHERE
            table_schema = 'public'""")
        else:
            self.cur.execute("""SELECT table_name FROM
            information_schema.tables""")
        tables: list(tuple) = self.cur.fetchall()
        tables: list = [t[0] for t in tables]
        return tables

    def _get_table_columns(self) -> list:
        """

        :param table_name: str, name of table
        :return: list, column names of table
        """
        query = sql.SQL(
            "SELECT * FROM {table} LIMIT 0").format(
            table=sql.Identifier(self.config["table_name"])
        )
        self.cur.execute(query)
        col_names = [desc[0] for desc in self.cur.description]

        return col_names

    def get_rows(self,
                 table_name: str) -> pd.DataFrame:
        """
        Extract data from an existing table.

        :param str: table_name, name of table in PostgreSQL database
        """
        df: pd.DataFrame = pd.read_sql_query(sql=f"SELECT * FROM {table_name}",
                                             con=self.connection)
        return df

    # Manipulate connected PostgreSQL
    # ------------------------------------------------------------------
    def _create_table(self,
                      query: str) -> None:
        """
        Creates a table in the currently connected database with a
        given query.

        :param query: str, table structure
        """
        try:
            self.cur.execute(query)
            self.connection.commit()

        except psycopg2.DatabaseError as e:
            logging.error("%s", e)
            self.connection.rollback()

    def _insert_in_table(self,
                         data: dict) -> None:
        """
        Inserts a row with data to a specific table.

        :param data: dict, data to parse
        """
        try:
            query = sql.SQL("INSERT INTO {table} ({fields}) VALUES({values})").format(
                            table=sql.Identifier(self.config["table_name"]),
                            fields=sql.SQL(",").join(map(sql.Identifier, data)),
                            values=sql.SQL(",").join(map(sql.Placeholder, data))
                            )
            self.cur.execute(query, data)
            self.connection.commit()

        except (psycopg2.ProgrammingError, psycopg2.DataError) as e:
            logging.error("%s", e)
            self.connection.rollback()
            self.close_connection()
            sys.exit()

    def _insert_in_table_copy(self) -> None:
        start: int = time.time()
        buffer = StringIO()
        buffer.write(self.df.to_csv(index=False, header=False, sep=";"))
        buffer.seek(0)

        try:
            self.cur.copy_from(buffer,
                               self.config["table_name"],
                               sep=";")
            self.connection.commit()
            print(f"Storing into database took {time.time() - start}")
        except psycopg2.DatabaseError as e:
            print(e)
            self.connection.rollback()
            self.connection.close()

    def update_rows(self,
                    col_to_update: str,
                    col_condition: str) -> None:
        """
        ABC
        :param col_to_update: str, name of column in database to update
        """
        try:
            for _, row in self.df.iterrows():
                query = sql.SQL("UPDATE {table} SET {field}=%s WHERE {field2}={value2}").format(
                                table=sql.Identifier(self.config["table_name"],),
                                field=sql.Identifier(col_to_update),
                                field2=sql.Identifier(col_condition),
                                value2=sql.Identifier(row[col_condition])
                                )
                self.cur.execute(query, (row[col_to_update],))
                self.connection.commit()

        except (psycopg2.ProgrammingError, psycopg2.DataError) as e:
            logging.error("%s", e)
            self.connection.rollback()
            self.close_connection()
            sys.exit()

    def close_connection(self):
        """
        Terminates an existing PostgreSQL connection.
        """
        self.connection.close()
    