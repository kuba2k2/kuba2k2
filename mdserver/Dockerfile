FROM python:3.11-alpine

WORKDIR /app

ENV SETTINGS_DIR=/data

RUN pip install --no-cache-dir poetry==1.8.3

COPY pyproject.toml poetry.lock .

RUN poetry install

COPY mdserver ./mdserver

CMD [ "poetry", "run", "python", "-m", "mdserver" ]
