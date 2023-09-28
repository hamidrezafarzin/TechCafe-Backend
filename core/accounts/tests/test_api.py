from rest_framework.test import APIClient
from django.urls import reverse
import pytest


class TestPostApi:
    def test_get_post_response_200_status(self):
        client = APIClient()
        url = reverse("profile")
        response = client.get(url)
        assert response.status_code == 200

    def test_create_post_response_401_status(self):
        url = reverse()
        data = {
            "phone": "09121234567",
            "first_name": "test_first_name",
            "last_name": "test_last_name",
            "language": "Python",
            "framework": "django",
        }
        response = self.client.post(url, data)
        assert response.status_code == 401
