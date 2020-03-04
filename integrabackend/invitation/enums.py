from django.apps import apps


class DefaultEnums:
    _model = None

    def create_default(self):
        if not self._model:
            raise ValueError("Need set model attribute")

        for key in self.__dir__():
            if '_' in key:
                continue
            
            value = getattr(self, key)
            self._model.objects.get_or_create(name=value)


class MedioEnums(DefaultEnums):
    _model = apps.get_model('invitation', 'Medio')

    automobile = 'Automobile'
    motorcicle = 'Motorcicle'
    taxi = 'Taxi'
    truck = 'Truck'
    walking = 'Walking'
