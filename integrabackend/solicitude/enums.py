from django.db.models import Q


class StateSolicitudeServiceEnums:
    draft = 'x'

    @property
    def limit_choice(self):
        return Q(name=self.draft)


class StateEnums:
    service_request = StateSolicitudeServiceEnums()