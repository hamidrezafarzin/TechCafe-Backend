import logging
from django.urls import reverse
from django.shortcuts import render
from azbankgateways import (
    bankfactories,
    models as bank_models,
    default_settings as settings,
)
from azbankgateways.exceptions import AZBankGatewaysException
from gathering.models import GatheringUser
from rest_framework.response import Response
from rest_framework import status


class Gateway:
    def __init__(self, request):
        self.request = request

    def go_to_gateway_view(self, amount, object_id):
        try:
            gathering_user = GatheringUser.objects.get(id=object_id)
        except GatheringUser.DoesNotExist:
            return {
                "success": False,
                "context": None,
                "error": "GatheringUser object Not Found",
                "object_DoesNotExist": True,
            }
        else:
            amount = amount
            user_mobile_number = self.request.user.phone

            factory = bankfactories.BankFactory()
            try:
                bank = (
                    factory.auto_create()
                )  # or factory.create(bank_models.BankType.BMI) or set identifier
                bank.set_request(self.request)
                bank.set_amount(amount)
                # callback url
                bank.set_client_callback_url(
                    reverse("gathering:api-v1:event-register-gateway-callback")
                )  # reverse('callback-gateway')
                bank.set_mobile_number(user_mobile_number)

                # bank record
                bank_record = bank.ready()

                # add bank record for object in GatheringUser
                gathering_user.bank_gateway = bank_record
                gathering_user.save()

                # هدایت کاربر به درگاه بانک
                context = bank.get_gateway()
                return {
                    "success": True,
                    "context": context,
                    "error": None,
                    "object_DoesNotExist": False,
                }
            except AZBankGatewaysException as e:
                logging.critical(e)
                return {
                    "success": False,
                    "context": None,
                    "error": e,
                    "object_DoesNotExist": False,
                }

    def callback_gateway_view(self):
        tracking_code = self.request.GET.get(settings.TRACKING_CODE_QUERY_PARAM, None)
        if not tracking_code:
            return {
                "success": False,
                "context": None,
                "error": "invalid Link",
                "object_DoesNotExist": False,
            }

        try:
            bank_record = bank_models.Bank.objects.get(tracking_code=tracking_code)
        except bank_models.Bank.DoesNotExist:
            logging.debug("invalid Link")
            return {
                "success": False,
                "context": None,
                "error": "invalid Link",
                "object_DoesNotExist": False,
            }

        if bank_record.is_success:
            try:
                gathering_user_obj = GatheringUser.objects.get(bank_gateway=bank_record)
            except GatheringUser.DoesNotExist:
                return {
                    "success": False,
                    "context": None,
                    "error": "Not Found",
                    "object_DoesNotExist": True,
                }
            else:
                gathering_user_obj.is_paid = True
                gathering_user_obj.save()

            return {
                "success": True,
                "context": "Payment was successful",
                "error": None,
                "object_DoesNotExist": False,
            }

        # پرداخت موفق نبوده است. اگر پول کم شده است ظرف مدت ۴۸ ساعت پول به حساب شما بازخواهد گشت.
        return {
            "success": False,
            "context": None,
            "error": "پرداخت با شکست مواجه شده است. اگر پول کم شده است ظرف مدت ۴۸ ساعت پول به حساب شما بازخواهد گشت.",
            "object_DoesNotExist": False,
        }
