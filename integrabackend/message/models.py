from django.db import models
from integrabackend.contrib.models import BaseModel

# Create your models here.

class Message(BaseModel):
    code = models.CharField('CODE', max_length=50, unique=True)
    message = models.TextField()
    message_es = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.code
