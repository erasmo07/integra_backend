# -*- coding: utf-8 -*-
from django.test import TestCase
from ...permissions import HasCreditPermission
from mock import patch, MagicMock
from django.test import tag
from ....users.test.factories import UserFactory
from ....resident.test.factories import ResidentFactory


class HasCreditPermissionTest(TestCase):

    def setUp(self):
        self.permission = HasCreditPermission()
        self.view = MagicMock()

    def get_request(self, sap_customer):
        user = UserFactory.create()
        ResidentFactory(
            user=user, sap_customer=sap_customer)
        request = MagicMock(user=user)
        return request

    @tag('integration')
    def test_permission_class_returns_true_if_resident_has_credit(self):
        # Arrange
        request = self.get_request(4259)

        # Act and Assert
        self.assertTrue(self.permission.has_permission(request, self.view))

    @tag('integration')
    def test_permission_class_returns_false_if_resident_has_not_credit(self):
        # Arrange
        request = self.get_request(4635)

        # Act and Assert
        self.assertFalse(self.permission.has_permission(request, self.view))

    @tag('unit')
    @patch('partenon.ERP.ERPClient.has_credit')
    def test_permission_class_returns_true_if_resident_has_credit_unit(self, mock_has_credit):
        # Arrange
        mock_has_credit.return_value = {
            "puede_consumir": True
        }
        request = self.get_request(4259)

        # Act and Assert
        self.assertTrue(self.permission.has_permission(request, self.view))

    @tag('unit')
    @patch('partenon.ERP.ERPClient.has_credit')
    def test_permission_class_returns_false_if_resident_has_no_credit_unit(self, mock_has_credit):
        # Arrange
        mock_has_credit.return_value = {
            "puede_consumir": False
        }
        request = self.get_request(4259)

        # Act and Assert
        self.assertFalse(self.permission.has_permission(request, self.view))
