from celery.decorators import task
from celery.utils.log import get_task_logger
from integrabackend.celery import app

from integrabackend.solicitude import models, helpers


logger = get_task_logger(__name__)


@app.task(name="create_service_request")
def create_service_request(service_request_id):
    """sends an email when feedback form is filled successfully"""
    logger.info("Buscando la solicitu de servicio #%s" % service_request_id)
    service_request = models.ServiceRequest.objects.get(pk=service_request_id)
    logger.info("Creando solicitud de servicio en sistemas externos")
    helpers.create_service_request(service_request)