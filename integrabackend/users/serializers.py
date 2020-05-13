from rest_framework import serializers
from .models import User, Application, Merchant


class UserSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        # call create_user on user object. Without this
        # the password will be stored in plain text.
        user = User.objects.create_user(**validated_data)
        return user

    class Meta:
        model = User
        fields = (
            'id', 'username', 'password', 'first_name',
            'last_name', 'email', 'auth_token', 'resident',
            'last_login', 'date_joined', 'is_active')
        read_only_fields = (
            'auth_token', 'resident',
            'last_login', 'date_joined',
            'is_active') 
        extra_kwargs = {'password': {'write_only': True}}


class ApplicationSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Application
        fields = ('id', 'name')


class MerchantSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Merchant
        fields = '__all__' 
        read_only_fields = ('id', )