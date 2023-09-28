from django.contrib.auth import get_user_model
from django.test import TestCase
from gathering.models import Gathering
from datetime import datetime


class EventModelsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user_obj = User.objects.create_user(
            phone="00000000000", password="a/@1234567"
        )

    def test_create_event_with_valid_data(self):
        # create Event Object With valid data
        event_obj = Gathering.objects.create(
            title="test_title",
            description="test_description",
            poster="test.png",
            address="test_address",
            price=1.000,
            link="https://www.google.com",
            date=datetime.now(),
            max_seats="5",
            is_online=True,
            is_held=False,
            is_occupied=False,
        )
        # add presenter to event
        event_obj.presenter.add(self.user_obj)

        self.assertEqual(event_obj.presenter.count(), 1)
        self.assertIn(self.user_obj, event_obj.presenter.all())
        self.assertEqual(event_obj.title, "test_title")
        self.assertFalse(event_obj.is_held)
        self.assertFalse(event_obj.is_held)
        self.assertTrue(event_obj.is_online)
