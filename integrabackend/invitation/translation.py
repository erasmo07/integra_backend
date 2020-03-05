from modeltranslation.translator import translator, TranslationOptions
from . import models


class ColorTranslationOptions(TranslationOptions):
    fields = ('name', )


class MedioTranslationOptions(TranslationOptions):
    fields = ('name', )


translator.register(models.Color, ColorTranslationOptions)
translator.register(models.Medio, MedioTranslationOptions)