from django.db.models import Q


class StateSolicitudeServiceEnums:
    draft = 'x'
    notify_cotization = 'Espera de aprobacion'

    @property
    def limit_choice(self):
        return Q(name=self.draft)


class StateEnums:
    service_request = StateSolicitudeServiceEnums()


class Subjects:
    aprove_or_reject_service = "Aprovar o Rechazar cotizacion"