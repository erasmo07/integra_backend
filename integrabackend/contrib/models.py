from django.db import models
import uuid


class BaseModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)

    class Meta:
        abstract = True


class BaseStatus(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(max_length=50)

    class Meta:
        abstract = True

    def __unicode__(self):
        """Unicode representation of StatusDocument."""
        return self.name