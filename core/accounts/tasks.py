from celery import shared_task
from adapter.melipayamak import Api
from decouple import config

username = config("MELIPAYAMAK_USERNAME", default="test")
password = config("MELIPAYAMAK_PASSWORD", default="test")


@shared_task
def send_otp(phone, code):
    api = Api(username, password)
    sms_rest = api.sms()
    to = phone
    text = [
        f"{code}",
    ]
    bodyId = 115131

    response = sms_rest.send_by_base_number(text, to, bodyId)
    if len(response["Value"]) >= 15:
        return True
    else:
        return False


@shared_task
def send_welcome(phone, first_name):
    api = Api(username, password)
    sms_rest = api.sms()
    to = phone
    text = [
        f"{first_name}",
    ]
    bodyId = 115128

    response = sms_rest.send_by_base_number(text, to, bodyId)
    if len(response["Value"]) >= 15:
        return True
    else:
        return False
