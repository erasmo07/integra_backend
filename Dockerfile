FROM python:3.6
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SECRET_KEY=local

ENV FAVEO_USERNAME=admin
ENV FAVEO_ADMIN_EMAIL=aplicaciones@puntacana.com
ENV FAVEO_PASSWORD=Nomelose123
ENV FAVEO_BASE_URL=http://faveo.grupopuntacana.com/

ENV FAVEO_DB_BASE_URL=http://172.30.101.48:5002/
ENV SITA_DB_BASE_URL=http://172.30.101.48:5000/
ENV SITAAMS_URL=http://172.30.20.12/SITAAMSIntegrationService/v2/SITAAMSIntegrationService
ENV SITAAMS_ACTION=http://www.sita.aero/ams6-xml-api-webservice/IAMSIntegrationService/GetFlights
ENV SITAAMS_TOKEN=6aed03fa-93f1-4733-b71d-a25935e318df

ENV SAP_USERNAME=dchot
ENV SAP_PASSWORD=1234567
ENV SAP_BASE_URL=http://athena.grupopuntacana.com:8000/
ENV SAP_AUTHENTICATION_URL=/api_portal_clie/info_aviso?sap-client=300
ENV SAP_CLIENT=300

ENV HERMES_UID=18297613965
ENV HERMES_BASE_URL=https://hermes:8000/
ENV HERMES_TOKEN=3f21d120491cb380c3d2aeb632a1d2885b8e7f625f6e4

# AZUL
ENV AZUL_CURRENCYPOSTCODE='$'
ENV AZUL_ECOMMERCE_URL='https://app.puntacana.com'
ENV AZUL_CHANNEL='EC'
ENV AZUL_POSINPUMODE='E-Commerce'
ENV AZUL_MERCHAN_NAME='puntacana'
ENV AZUL_HOST='pruebas.azul.com.do'

ENV AZUL_39038540035_AUTH_ONE='testcert2'
ENV AZUL_39038540035_AUTH_TWO='testcert2'

ENV AZUL_PATH_CSR='puntacana_v2.csr'
ENV AZUL_CERTIFICATE_PATH='cert-puntacana.txt'
ENV AZUL_CERTIFICATE_KEY_PATH='puntacana_v2.key'


# Allows docker to cache installed dependencies between builds
COPY ./requirements.txt requirements.txt
COPY ./cert-puntacana.txt cert-puntacana.txt
COPY ./puntacana_v2.key puntacana_v2.key
COPY ./puntacana_v2.csr puntacana_v2.csr

RUN sed -i -E 's/MinProtocol[=\ ]+.*/MinProtocol = TLSv1.0/g' /etc/ssl/openssl.cnf

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Adds our application code to the image
COPY . code
WORKDIR code

EXPOSE 8000

# Migrates the database, uploads staticfiles, and runs the production server
CMD ./manage.py migrate && \
    ./manage.py collectstatic --noinput && \
    newrelic-admin run-program gunicorn --workers 4 --bind 0.0.0.0:8000 --timeout=120 --access-logfile - integrabackend.wsgi:application
