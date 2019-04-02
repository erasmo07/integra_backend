from rest_framework.pagination import PageNumberPagination


class ServiceRequestPaginate(PageNumberPagination):
    page_size = 10
