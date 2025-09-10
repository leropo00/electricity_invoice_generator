FROM python:3.13-alpine

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
WORKDIR /app

RUN  apk add --no-cache postgresql-libs &&  apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev 

RUN  apk add --no-cache glib pango

RUN  apk add --no-cache fontconfig  ttf-dejavu  ttf-freefont

RUN uv sync --frozen --no-cache


CMD ["uv", "run", "fastapi", "dev", "--host", "0.0.0.0"]

