from django.contrib import admin


def display_all(model):
    """ Function to list all element of one model. """
    return [field.name for field in model._meta.fields
            if field.name != "id"]