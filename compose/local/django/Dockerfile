# define an alias for the specific python version used in this file.
FROM docker.io/python:3.11-slim AS python

# Python build stage
FROM python AS python-build-stage

ARG BUILD_ENVIRONMENT=local

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y --fix-missing \
  # dependencies for building Python packages
  build-essential \
  # psycopg dependencies
  libpq-dev \
  # mysqlclient dependencies
  pkg-config \
  default-libmysqlclient-dev \
  libmariadb-dev

# Диагностика: убедиться, что pkg-config в PATH
RUN apt-get update && which pkg-config && echo $PATH

# На всякий случай явно расширяем PATH
ENV PATH="/usr/bin:/usr/local/bin:${PATH}"
# Set MySQL client flags for building mysqlclient wheel, in case pkg-config is problematic
# These paths should be valid after default-libmysqlclient-dev is installed.
ENV MYSQLCLIENT_CFLAGS="-I/usr/include/mysql"
ENV MYSQLCLIENT_LDFLAGS="-L/usr/lib/x86_64-linux-gnu -lmysqlclient"

# Requirements are installed here to ensure they will be cached.
COPY ./requirements ./requirements

# Создаём временный requirements файл в /tmp, корректируя пути для -r опций
RUN sed 's/^-r \(.*\)/-r ..\/requirements\/\1/g' requirements/${BUILD_ENVIRONMENT}.txt | grep -iv '^mysqlclient' > /tmp/reqs.txt

# Сначала wheels для всех зависимостей кроме mysqlclient, используя скорректированный /tmp/reqs.txt
RUN pip wheel --wheel-dir /usr/src/app/wheels --no-cache-dir -r /tmp/reqs.txt

# Диагностика перед сборкой wheel для mysqlclient
RUN echo "Running pkg-config diagnostic for mariadb or mysqlclient" && (pkg-config --cflags --libs mariadb || pkg-config --cflags --libs mysqlclient || echo "pkg-config failed for both mariadb and mysqlclient")

# Затем wheel для mysqlclient без build isolation, с явно установленными переменными окружения
# Ensure MYSQLCLIENT_CFLAGS and MYSQLCLIENT_LDFLAGS are correctly passed for this specific command
RUN MYSQLCLIENT_CFLAGS="${MYSQLCLIENT_CFLAGS}" MYSQLCLIENT_LDFLAGS="${MYSQLCLIENT_LDFLAGS}" \
    pip wheel --wheel-dir /usr/src/app/wheels --no-cache-dir --no-build-isolation mysqlclient==2.2.0


# Python 'run' stage
FROM python AS python-run-stage

ARG BUILD_ENVIRONMENT=local
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV BUILD_ENV=${BUILD_ENVIRONMENT}
ENV MYSQLCLIENT_CFLAGS="-I/usr/include/mysql" \
    MYSQLCLIENT_LDFLAGS="-L/usr/lib/x86_64-linux-gnu -lmysqlclient"

WORKDIR ${APP_HOME}


# Install required system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y --fix-missing \
    # psycopg dependencies
    libpq-dev \
    # Translations dependencies
    gettext \
    pkg-config \
    default-libmysqlclient-dev \
    libmariadb-dev \
    # For downloading wait-for-it
    curl \
    && echo "Downloading wait-for-it" \
    && curl -o /usr/local/bin/wait-for-it https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh \
    && chmod +x /usr/local/bin/wait-for-it \
    # Clean up
    && apt-get purge -y --auto-remove curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Ensure Python wheels are installed correctly
COPY --from=python-build-stage /usr/src/app/wheels /wheels/
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ --only-binary=:all: /wheels/* \
  && rm -rf /wheels/

# Copy and prepare entrypoint script
COPY ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint && chmod +x /entrypoint

# Copy and prepare start script
COPY ./compose/local/django/start /start
RUN sed -i 's/\r$//g' /start && chmod +x /start

# Copy and prepare Celery scripts
COPY ./compose/local/django/celery/worker/start /start-celeryworker
RUN sed -i 's/\r$//g' /start-celeryworker && chmod +x /start-celeryworker

COPY ./compose/local/django/celery/beat/start /start-celerybeat
RUN sed -i 's/\r$//g' /start-celerybeat && chmod +x /start-celerybeat

COPY ./compose/local/django/celery/flower/start /start-flower
RUN sed -i 's/\r$//g' /start-flower && chmod +x /start-flower


# Copy application code to WORKDIR
COPY . ${APP_HOME}

# Set entrypoint
ENTRYPOINT ["/entrypoint"]
