FROM python:3.6
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SECRET_KEY=local

ENV FAVEO_USERNAME=admin
ENV FAVEO_PASSWORD=Nomelose123
ENV FAVEO_BASE_URL=http://faveo.grupopuntacana.com:81/

ENV FAVEO_DB_BASE_URL=http://87.4.5.140:5002/

ENV SAP_USERNAME=dchot
ENV SAP_PASSWORD=1234567
ENV SAP_BASE_URL=http://athena.grupopuntacana.com:8000/
ENV SAP_CLIENT=300

ENV HERMES_UID=18297613965
ENV HERMES_BASE_URL=https://hermes:8000/
ENV HERMES_TOKEN=3f21d120491cb380c3d2aeb632a1d2885b8e7f625f6e4

# Allows docker to cache installed dependencies between builds
COPY ./requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Adds our application code to the image
COPY . code
WORKDIR code

EXPOSE 8000

# Migrates the database, uploads staticfiles, and runs the production server
CMD ./manage.py migrate && \
    ./manage.py collectstatic --noinput && \
    newrelic-admin run-program gunicorn --bind 0.0.0.0:8000 --access-logfile - integrabackend.wsgi:application
