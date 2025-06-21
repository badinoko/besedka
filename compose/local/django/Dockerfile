# define an alias for the specific python version used in this file.
FROM python:3.11-slim-buster

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update \
  && apt-get install -y build-essential \
  && apt-get install -y libpq-dev \
  && apt-get install -y gettext \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# Requirements are installed here to ensure they will be cached.
COPY ./requirements /requirements
RUN pip install -r /requirements/local.txt

WORKDIR /app

# Copy project
COPY . /app/

# Create media & static directories
RUN mkdir -p /app/media /app/static

# Run as non-root user
RUN useradd -m user
RUN chown -R user:user /app
USER user
