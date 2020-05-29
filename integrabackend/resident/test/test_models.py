
from django.test import TestCase
from nose.tools import eq_, ok_

from ...users.test.factories import UserFactory
from .. import models
from . import factories


class TestAreaPermision(TestCase):
    
    def setUp(self):
        self.model = models.AreaPermission
    
    def test_can_assign_area_to_user(self):
        # GIVEN
        area = factories.AreaFactory.create()
        user = UserFactory.create()
    
        # WHEN
        self.model.objects.create(area=area, user=user)
    
        # THEN
        ok_(user.areapermission_set.filter(area=area).exists())
