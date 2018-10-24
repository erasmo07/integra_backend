from django.test import TestCase
from django.forms.models import model_to_dict
from nose.tools import eq_, ok_
from .factories import ResidentFactory
from ..serializers import ResidentSerializer
from ...users.test.factories import UserFactory


class TestResidentSerializer(TestCase):

    def setUp(self):
        self.data = model_to_dict(ResidentFactory(user=UserFactory.create()))

    def test_serializer_with_empty_data(self):
        serializer = ResidentSerializer(data={})
        eq_(serializer.is_valid(), False)

    def test_serializer_with_valid_data(self):
        serializer = ResidentSerializer(data=self.data)
        ok_(serializer.is_valid())

    def test_serializer_hashes_password(self):
        serializer = ResidentSerializer(data=self.data)
        ok_(serializer.is_valid())

        resident = serializer.save()
        eq_(resident.name, self.data.get('name'))
        eq_(resident.email, self.data.get('email'))
        eq_(resident.telephone, self.data.get('telephone'))
        ok_(resident.is_active)
