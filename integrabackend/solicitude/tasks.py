from celery.decorators import task
from celery.utils.log import get_task_logger
from integrabackend.celery import app

from integrabackend.solicitude import models, helpers
from integrabackend.resident.models import ProjectService, Department
from partenon.helpdesk import Topics


logger = get_task_logger(__name__)


@app.task(name="create_service_request")
def create_service_request(service_request_id):
    """sends an email when feedback form is filled successfully"""
    logger.info("Buscando la solicitu de servicio #%s" % service_request_id)
    service_request = models.ServiceRequest.objects.get(pk=service_request_id)

    logger.info("Creando solicitud de servicio en sistemas externos")
    helpers.create_service_request(service_request)


@app.task(name='create_service_from_faveo')
def create_services_from_faveo():
    logger.info("Buscando los helptopic de faveo")
    for topic in Topics.objects.get_entitys():
        service, create = models.Service.objects.get_or_create(
            name=topic.topic, sap_code_service='S4')
        logger.info(f"Helptopic {service.name} was create {create}")

        department = Department.objects.filter(fave_id=topic.department)
        if not department.exists():
            continue

        logger.info(f"Relating {service.name} with {department.first().name}")
        project_service = ProjectService.objects.filter(
            project__department=department.first())
        if project_service.exists():
            project_service.first().services.add(service)
            logger.info(f"Related {service.name} with {department.first().name}")