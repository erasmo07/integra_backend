from rest_framework import serializers
from . import models


class UserSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        # call create_user on user object. Without this
        # the password will be stored in plain text.
        user = models.User.objects.create_user(**validated_data)
        return user

    class Meta:
        model = models.User
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
        model = models.Application
        fields = ('id', 'name')


class AccessDetail(serializers.ModelSerializer):

    class Meta:
        model = models.AccessDetail
        fields = "__all__"
        read_only_fields = ('id', )


class AccessApplicationSerializer(serializers.ModelSerializer):
    application = ApplicationSerializer()
    details = AccessDetail(many=True)

    class Meta:
        model = models.AccessApplication
        fields = '__all__'
        read_only_fields = ('id', )


class MerchantSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = models.Merchant
        fields = '__all__' 
        read_only_fields = ('id', )