# Electricity Invoice Generator

Project using Python, FastAPI, uv package manager and Timescaledb database. 
TimescaleDB is a PostgreSQL extension for timeseries data.
Alembic library is used to run migrations.

## How to setup 
Docker is needed to run the containers. Move to the root folder of project and run command:

```
docker-compose up -d
```

You need to copy .env.example file to .env file for project settings.
Uncomment value bellow, and comment out sample value for DATABASE_URI:

```
DATABASE_URI=postgresql://postgres:password@timescaledb/electricity_invoices
```

This property is also repeated in file alembic.ini, which contains definitions for alembic migration tool
sqlalchemy.url = postgresql://postgres:password@timescaledb/electricity_invoices




After running container, you need to run alembic migrations to create tables.

```sh
# enter the container
docker exec -it fastapi-app sh
# run migrations that creates tables and fills some data
.venv/bin/alembic upgrade head
# leave the container
exit
```

Since FastAPI is used, after starting project,
Swagger with all endpoints is present on url:
http://localhost:8000/docs


I used DBeaver to check database state during developement, 
if using default settings from container, add this string as connection:
jdbc:postgresql://localhost:5433/electricity_invoices and use username,password from docker compose definition.


## Alternatively you could also run only timescaledb service in container and use local installation of Python.

In this case you should set DATABASE_URI property in .env file and property sqlalchemy.url in alembic.ini to this value:
postgresql://postgres:password@localhost:5433/electricity_invoices
If using local Python it is recommended to create virtual environment.
Uv package manager is recommended for usage:

### 1. Uv installation

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.13
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Create a virtual environment with all necessary dependencies

From the root of the project execute:

```bash
uv sync
```

### 3. Run server in development mode

```bash
uv run fastapi dev
```



## Application usage

Certain data, like the default electricity provider, is already created via migrations.
You can also add  additional providers.
But you need to create the needed customer via endpoint /customers,
to parse .csv files.
After you create a customer, you also need to create customer contracts with the selected provider.
Only then will you have enough data to create an invoice.

A customer can have only one active contract at a time.
To create a new contract, you have to terminate the active contract via endpoint .

For the measurement .csv file to be valid, it should be in the form filename-{id}.csv.

In this example, the filename could be anything; {id} should be the customer_id in the database.
Last '-' is a separator between {id}, and the filename must end with .csv.
Capitalization is ignored in the filename.
CSV file should use semicolon ';' for separation of values.

After measurements from CSV were parsed, you can store invoice data.
You always create an invoice for a specific month, year, and only a certain customer_id.
You need to provide all 3 parameters.
After you have created an invoice record, you can then create an invoice PDF document. 
This has no effect on the database state.

An invoice is considered immutable, so after creation, you can't change the data.
You need to delete it and recreate it.
You can always recreate an invoice for selected combinations of 3 input parameters.
Invoice items are calculated based on definitions of time blocks,
this was used as a reference for data definitions.

https://www.uro.si/w/casovni-blok

These definitions are parsed via migrations,
But there are no endpoints to change these definitions.

