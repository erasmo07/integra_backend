# -*- coding: utf-8 -*-
from rest_framework.test import APITestCase
from django.urls import reverse
from django.test import tag
from rest_framework import status
from ....users.test.factories import UserFactory


class ResidentHasCreditTest(APITestCase):

    def setUp(self):
        self.base_name = 'client_has_credit'
        self.url = reverse('%s-list' % self.base_name)

        self.client.force_authenticate(user=UserFactory.build())

    def tearDown(self):
        pass

    @tag('integration')
    def test_check_a_resident_has_credit(self):
        # Arrange
        url = self.url + '?code=4259'
        expected = {
            "puede_consumir": True
        }

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected)

    @tag('integration')
    def test_check_a_resident_has_not_credit(self):
        # Arrange
        url = self.url + '?code=4635'
        expected = {
            "puede_consumir": False
        }

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected)
