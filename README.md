# The Mobility House Coding Challenge
This README explains all steps required to collect, process, and query information about curtailment of power generation in the balance zone of the transmission system operator (TSO) TenneT GmbH in Germany. Data ranges from 1st of January 2022 to 31th of December 2022.

- [Explanations](#explanations)
  - [Dataset](#dataset)
  - [Database](#database)
- [Setting Up The Environment](#environment)
  - [Deploy Virtual Machine](#vm_deploy)
  - [Initialize Virtual Machine](#vm_init)
  - [Configure Database](#database_init)
- [Example Code](#example_code)
- [Open End Question](#open_end_question)

## Explanations <a name="explanations"></a>
The task is to extract data from two different data sources (1. Abgeschlossene Maßnahmen, 2. EEG-Analgenstammdaten), merge them with each other based on their "EEG Anlagenschlüssel" and lastly, calculate the curtailed power and energy.

### Dataset <a name="dataset"></a>
However, none of those two datasets contain information about the nominal power of each power plant. Additionally, only the first dataset dates back to 2020 or 2021. The provided [link](https://www.netztransparenz.de/EEG/Anlagenstammdaten) for the 2nd dataset only points to data for 2022. I did not receive a response from the website provider to my request about how to access the data from 2020 or 2021. Therefore, I test my solution with data from 2022.

I scrapped the [Marktstammdatenregister](https://www.marktstammdatenregister.de/MaStR/Einheit/Einheiten/ErweiterteOeffentlicheEinheitenuebersicht) to get the nominal power of each power plant. The 2nd dataset contains information about the Marktstammdaten number for NBs (NB_Mastr_Nr). Filtering with this number the Marktstammdatenregister database returns a lot of information of the installed power plants in the balance zone of that specific network operator, including the nominal power.

The data should also focus on the balance zone of TenneT GmbH. However, the provided example [request](https://redispatch-run.azurewebsites.net/api/export/csv?&networkoperator=ava&type=finished&rderDirection=desc&orderBy=start&chunkNr=1&param1=start&op1=gt&startOp=gt&val1=2022-04-01&param2=end&op2=equals&endOp=eq&val2=2022-08-31) to obtain dataset 1 via the API uses the network operator Avacon. This network operator operates also outside of TenneTs balance zone (e.g., Nordrhein-Westfalen). Nevertheless, to reduce complexity I stick to this network operator.

### Database <a name="database"></a>
The goal is to give all users working on the database as few priviliges as necessary. For example, the client-side plotting the data only needs read access. For the server-side I first limited its privileges to read (SELECT) and write (INSERT). However, I had througput and latency issues with updating the database. As a work around I therefore gave the server also delete (TRUNCATE) rights to replace the entire database instead of updating only a few columns. This needs further improvments for production systems to avoid false reads from clients while working with the database. I tried the following approaches to update the table, but all of them requried more than a few seconds execution time:

- Updating and commiting in a for-loop
- Updating in a for-loop and only commit every 10,000th entry
- Use `executemany` and `execute_batch`
- Updating by using integer index for the `WHERE` condition instead of the plant_id column, which is `VARCHAR` (e.g., `UPDATE "curtailments" SET "power_curtailed"=%s WHERE "idx"=%`)

Further improvments include using smaller data types for the columns where applicable. For example, `SMALLINT` for power_nominal instead of `NUMERIC`. However, this requires checks before writing anything to the database to avoid errors.

## Setting Up The Environment <a name="environment"></a>
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
Set up a PostgreSQL database with two users. First, connect to PostgreSQL `sudo -u postgres psql` and list all available users with their respective priviliges `\du` / `SELECT * FROM information_schema.role_table_grants WHERE grantee='user_name';` or without their priviliges `SELECT usename from pg_catalog.pg_user;`. Create new users if no suitable users already exist for the server and client `CREATE USER tmh_type WITH ENCRYPTED PASSWORD 'tmh_type';`:

1. type=server: User to read and write data into an existing database
2. type=client: User with read-only access

Preparing database and tables:
1. Create database `SELECT 'CREATE DATABASE curtailment_tennet' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'curtailment_tennet')\gexec`
2. Connect to new database `\c curtailment_tennet`
3. Create table: `CREATE TABLE IF NOT EXISTS curtailments (start_curtailment TIMESTAMP, end_curtailment TIMESTAMP, duration SMALLINT, level SMALLINT, cause VARCHAR, plant_id VARCHAR, operator VARCHAR, power_nominal numeric, power_curtailed numeric, energy_curtailed numeric);`
4. Change user priviliges <br>
4.1 Give server and client read access `GRANT SELECT ON TABLE curtailments TO tmh_<type>;` <br>
4.2 Give server write access `GRANT INSERT ON TABLE curtailments TO tmh_server;`
4.3 Give server truncate access `GRANT TRUNCATE ON TABLE curtailments TO tmh_server;`

## Example Code <a name="example_code"></a>
```
# stdlib
import os
import logging

# third party
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
    df = avacon_api.call_api()

    # Clean extracted data
    process_data: ProcessData = ProcessData(df)
    process_data.clean()
    df = process_data.get_data()

    # Store cleaned data in PostgreSQL database based on query.json config
    psql: PostgreSQL = PostgreSQL(config_path=config_path,
                                  config_name="query.json",
                                  data=df)
    psql.connect_and_insert()

    # Scrap Marktstammdatenregister (might be optional)
    path_anlagenstammdaten: str = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                               "anlagenstammdaten")
    mapper: Mapping = Mapping(path_anlagenstammdaten,
                              "TenneT TSO GmbH EEG-Zahlungen Bewegungsdaten 2022.csv")
    if SCRAP_MASTR:
        scrapper: MastrScrapper = MastrScrapper()
        for nb_mastr_nr in mapper.get_nb_mastr_nrs():
            scrapper.set_nb_mastr_nr(nb_mastr_nr)
            scrapper.download_via_link()
            scrapper.move_downloaded_file()
        scrapper.merge_snbs_into_one_csv(path_anlagenstammdaten)

    # Update PostgreSQL database with values for nominal power and curtailed energy
    psql.connect_to_db()
    mapper.set_df(psql.get_rows("curtailments"))
    mapper.get_merged_snbs()
    mapper.create_mapping()
    mapper.map_power_to_plant_id()
    mapper.calculate_curtailed_power()
    mapper.calculate_curtailed_energy()

    psql.cur.execute("TRUNCATE curtailments;", )
    psql.connection.commit()
    psql.set_df(mapper.df_db)
    psql.close_connection()
    psql.connect_and_insert()


if __name__ == "__main__":
    main()
```

## Open End Question <a name="open_end_question"></a>
What can we do with the information about curtailed power and energy of specific power plants in a given region:
1. Identify patterns in time, type of power plant and location <br>
1.1 Time: Is wind power mostly curtailed at night or in the winter? Are PV fields curtailed at peak sun? <br>
1.2 Type of power: Are wind power plants curtailed more often than PV fields due to their large nominal power? It might be more efficient to shutdown one winder power plant with 5 MW instead of a bunch of PVs. <br>
1.3 Location: Identify bottlenecks in the grid by using power plants, which are more often curtailed then others of the same type. For example, I scrapped information about the postal code as well allowing to visualize the type of curtailments over time on a map. 
2. Enriching our dataset with weather data (e.g., sun irradation, temperature) to better understand the relation between curtailements and weather. For example, high irradation can lead to a higher chance of being curtailed for PV fields.
3. Enriching our dataset with electricity consumption to better understand the relations between curtailments and consumption. For example, peak-demand times (e.g., in the morning and evening or during large events such as festivals) are less prone for curtailments.
4. Trying to predict curtailed power and energy with linear regression and machine learning (ML) models by using weather, consumption, and information about the power grid as features / inputs. One could develop physically-informed ML models to consider grid transmission constraints.
5. Look abroad: Energy is bought where it is cheap. When France or Norway produce cheap electricity with their nuclear and hydro power plants, respectively, local power plants might be more prone for curtailments. This works both ways. For example, last year during summer France had to reduce the output of their nucelar power plants due to too warm river water and Norway produced less with their hydro power due to too low reservoir levels.
