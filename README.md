# Electricity Invoice Creator

A starter project using Python, FastAPI, uv package manager and Timescaledb database. 
TimescaleDB is a PostgreSQL extension for timeseries data.
Alembic library is used to run migrations.

## How to setup 
Docker is needed to run the containers. Move to the root folder of project and run command:

```
docker-compose up -d
```
You need to copy .env.example file to .env file for project settings. Change url to this based on default setting in docker compose.

```
DATABASE_URI=postgresql://postgres:password@localhost:5433/electricity_invoices
```


After running container, you need to run alembic migrations to create tables.

```sh
# enter the container
docker exec -it fastapi-app sh
# run migrations that creates tables and fills some data
alembic upgrade head
# leave the container
exit
```

Since FastAPI is used, after starting project,
swagger with all endpoints is present on url:
http://localhost:8000/docs


## Data needed for document parsing

Certain data like electricity provider data is already created via migrations.
But you need to create via enpoints suppliers and their contracts with selected provider, to have enough data to create invoice.

For measurement .csv file to be valid it should be in form filename-{id}.csv.

In this example filename could be anything, {id} should be a number of supplier id in database.
Last '-' is separator between id, filename must end with .csv.
Capitalization is ignored in filename.
Csv file should use semicolon ';' for separation of values.


### Alternative: how to run Run application outside docker

**MacOS (using `brew`)**

```bash
brew install python@3.13 uv
```

**Ubuntu/Debian**

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

## Command to run Run application outside docker


### Development mode

```bash
uv run fastapi dev
```

### Production mode

```bash
uv run fastapi run
```

## Testing

```bash
uv run pytest
```

### With coverage

```bash
uv run pytest --cov=app
```

### With coverage and HTML output

```bash
uv run pytest --cov-report html --cov=app
```

## Linting

```bash
uv run ruff check app/* tests/*
```

## Formatting

```bash
uv run ruff format app/* tests/*
```

