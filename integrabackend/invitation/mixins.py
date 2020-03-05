

class ModelTranslateMixin(object):
    
    def get_serializer_class(self):
        language = self.request.META.get('HTTP_ACCEPT_LANGUAGE') 
        return self.serializer_language.get(language, self.serializer_class)