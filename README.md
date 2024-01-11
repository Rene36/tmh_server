# The Mobility House Coding Challenge
This README explains all steps required to collect, process, and query information about curtailment of power generation in the balance zone of the transmission grid operator (TSO) TenneT GmbH in Germany. Data ranges from 1st of January 2020 to 30th of December 2020.

- [Setting Up The Environment](#environment)
  - [Deploy Virtual Machine](#vm_deploy)
  - [Initialize Virtual Machine](#vm_init)
  - [Configure Database](#database_init)
- [Example Code](#example_code)
- [Assumptions](#assumptions)

## Setting Up The Environment <a name="environment></a>
Operating system: Ubuntu 22.04 LTS

### Deploy Virtual Machine <a name="vm_deploy"></a>
Check if you have Terraform installed by running `terraform --help` in the terminal. If Terraform is not installed on your machine follow the install guide from [Hashicorp](https://developer.hashicorp.com/terraform/install). We provide an example Terraform configuration files to deply a virtual machine running on OpenNebula. Adjust the following parts to match your environment: 

config.tfvars:
- ON_USERNAME
- ON_PASSWD
- ON_GROUP

on_vms.tf:
- endpoint
- flowpoint

1. `terraform init`
2. `terraform plan -var-file=config.tfvars -out=infra.out`
3. `terraform apply infra.out`
4. `tearraform show` to get IP address of deployed virtual machine, which is requried for the next step
5. `terraform destroy -var-file=config.tfvars` (optional)

### Initialize Virtual Machine <a name="vm_init"></a>
Check if you have Ansible installed by running `ansible --help` in the terminal. If Ansible is not installed on your machine follow the install guide from [Ansible Documentation](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html). We install all required programs and packages on the previously deployed virtual machine via Ansible playbooks.

1. Define IP address(es) by using a host group (e.g., in /etc/ansible/hosts) and refering to it in the playbooks
2. Adjust host group in all following YAML files
3. Update virtual machine: `ansible-playbook udpate.yml`
4. Install PostgreSQL: `ansible-playbook postgres_install.yml`
5. Copy files to virtual machine: `ansible-playbook copy_files.yml --extra-vars '{"path_to_files": "path/to/files/with/trailing/backslash/"}'`
6. Install Python virtual environments for type= server or client: `ansible-playbook prepare_virtualenv.yml --extra-vars '{"type": "server"}'`


### Configure Database <a name="database_init"></a>
Set up a PostgreSQL database with two users. First, connect to PostgreSQL `sudo -u postgres psql` and list all available users with their respective priviliges `\du` / `SELECT * FROM information_schema.role_table_grants WHERE grantee='user_name'`
;` or without their priviliges `SELECT usename from pg_catalog.pg_user;`. Create new users if no suitable users already exist for the server and client `CREATE USER tmh_type WITH ENCRYPTED PASSWORD 'tmh_type';`:

1. type=server: User to read and write data into an existing database
2. type=client: User with read-only access

Preparing database and tables:
1. Create database `SELECT 'CREATE DATABASE curtailment_tennet' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'curtailment_tennet')\gexec`
2. Connect to new database `\c curtailment_tennet`
3. Create table: `CREATE TABLE IF NOT EXISTS curtailments (start_curtailment TIMESTAMP, end_curtailment TIMESTAMP, duration SMALLINT, level SMALLINT, cause VARCHAR, plant_id VARCHAR, operator VARCHAR, nominal_power smallint, energy numeric);`
4. Change user priviliges <br>
4.1 Give server and client read access `GRANT SELECT ON TABLE curtailments TO tmh_<type>;` <br>
4.2 Give server write access `GRANT INSERT ON TABLE curtailments TO tmh_server;`
4.3 Give server update access `GRANT UPDATE ON TABLE curtailments TO tmh_server;`

## Example Code <a name="example_code"></a>
```
# stdlib
import os
import logging

# third party
import pandas as pd

# relative
from tmh_server.mapping import Mapping
from tmh_server.avacon_api import AvaconAPI
from tmh_server.postgresql import PostgreSQL
from tmh_server.process_data import ProcessData
from tmh_server.mastr_scrapper import MastrScrapper


SCRAP_MASTR: bool = False

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(filename=os.path.join(os.getcwd(), "tmh.log"),
                    format="%(asctime)s,%(levelname)s,%(module)s:%(funcName)s:%(lineno)s,%(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                    level=logging.DEBUG)


def main():
    """
    Combines data extraction from Avacon API, cleaning the output,
    and storing it in a PostgreSQL database. Then scrap
    Marktstammdatenregister based on network operator ID to obtain
    mapping of EEG Anlagenschlüssel to nominal power (might be optional).
    Lastly, update values for nominal power and curtailed energy based
    on power plant ID.
    """
    # Extract information from Avacon API based on avacon_api.json config
    config_path: str = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                    "configs")
    avacon_api: AvaconAPI = AvaconAPI(config_path=config_path,
                                      config_name="avacon_api.json")
    df: pd.DataFrame = avacon_api.call_api()

    # Clean extracted data
    process_data: ProcessData = ProcessData(df)
    process_data.clean()
    df: pd.DataFrame = process_data.get_data()

    # Store cleaned data in PostgreSQL database based on query.json config
    psql: PostgreSQL = PostgreSQL(config_path=config_path,
                                  config_name="query.json",
                                  data=df)
    psql.connect_and_insert()

    # Scrap Marktstammdatenregister (might be optional)
    if SCRAP_MASTR:
        path_anlagenstammdaten: str = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                                   "anlagenstammdaten")
        mapper: Mapping = Mapping(path_anlagenstammdaten,
                                  "TenneT TSO GmbH EEG-Zahlungen Bewegungsdaten 2022.csv")

        scrapper: MastrScrapper = MastrScrapper()
        for nb_mastr_nr in mapper.get_nb_mastr_nrs():
            scrapper.set_nb_mastr_nr(nb_mastr_nr)
            scrapper.download_via_link()
            scrapper.move_downloaded_file()
        scrapper.merge_snbs_into_one_csv(path_anlagenstammdaten)

    # Update PostgreSQL database with values for nominal power and curtailed energy
    mapper.get_merged_snbs()
    mapper.create_mapping()
    mapper.set_df_db(psql.get_rows("curtailments"))
    mapper.map_power_to_plant_id()
    mapper.calculate_curtailed_power()
    mapper.calculate_curtailed_energy()

    psql.close_connection()
    psql.set_df(mapper.df_db)
    psql.update_rows(col_to_update="nominal_power",
                     col_condition="plant_id")


if __name__ == "__main__":
    main()
```


## Assumptions <a name="assumptions"></a>
Additional information, e.g.,
- AVACON does not exclusively operate in TenneT area
- Add code lintering