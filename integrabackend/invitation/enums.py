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


class TypeInvitationEnums(DefaultEnums):
    _model = apps.get_model('invitation', 'TypeInvitation')

    supplier = 'Supplier'
    friend_and_family = 'Friends and Family'


class MedioEnums(DefaultEnums):
    _model = apps.get_model('invitation', 'Medio')

    automobile = 'Automobile'
    motorcicle = 'Motorcicle'
    taxi = 'Taxi'
    truck = 'Truck'
    walking = 'Walking'


class ColorEnums(DefaultEnums):
    _model = apps.get_model('invitation', 'Color')

    blue = 'Blue'
    red = 'Red'
    orange = 'Orange'
    green = 'Green'
    black = 'Black'
    white = 'White'
    grey = 'Grey'
    gold = 'Gold'
    silver = 'Silver'
    yellow = 'Yellow'
    other = 'other'