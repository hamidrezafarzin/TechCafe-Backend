import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from utils.constants import Errors


class FieldValidators:
    def xss_validator(value):
        XSS_PATTERN = r"<(script|img|a|div|iframe|style)[^>]*>"
        if re.search(XSS_PATTERN, value):
            raise ValidationError(
                _(f"{Errors.XSS_ATTACK_DETECTION}"),
            )

    def iranian_phone_validator(value):
        IRANIAN_PHONE_PATTERN = r"^09\d{9}$"
        if not re.match(IRANIAN_PHONE_PATTERN, value):
            raise ValidationError(
                _(f"{Errors.INVALID_PHONE_NUMBER_PATTERN}"),
            )

    def otp_validator(value):
        OTP_PATTERN = r"^[0-9]{4}$"
        if not re.match(OTP_PATTERN, value):
            raise ValidationError(
                _(f"{Errors.INVALID_OTP_PATTERN}"),
            )
