from rest_framework import serializers
from accounts.models import User, Languages, Frameworks
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions
from django.core.cache import cache
from validators.fieldvalidators import FieldValidators
from utils.constants import Errors
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.conf import settings
from accounts.tasks import send_otp
import random
from rest_framework import status

# Serializer for user registration with password checkup
class RegisterSerializer(serializers.ModelSerializer):
    """Registration serializer with password checkup"""

    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    password1 = serializers.CharField(max_length=68, min_length=6, write_only=True)
    otp_code = serializers.CharField(
        max_length=4,
        validators=[FieldValidators.xss_validator, FieldValidators.otp_validator],
        write_only=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "otp_code",
            "first_name",
            "last_name",
            "password",
            "password1",
        ]
        required_fields = ["phone", "otp_code", "first_name", "last_name"]

    def validate(self, attrs):
        # Check if passwords match
        if attrs.get("password") != attrs.get("password1"):
            raise serializers.ValidationError(Errors.PASSWORD_MISMATCHED)

        # Validate OTP code
        if cache.get(f"register:{attrs.get('phone')}") != None:
            if attrs.get("otp_code") == cache.get(f"register:{attrs.get('phone')}"):
                cache.delete(f"register:{attrs.get('phone')}")
                attrs.pop("otp_code", None)
            else:
                raise serializers.ValidationError(Errors.INVALID_OTP_CODE)
        else:
            raise serializers.ValidationError(Errors.INVALID_OTP_CODE)
        return super().validate(attrs)

    def create(self, validated_data):
        if validated_data.get("email") == "":
            validated_data["email"] = None
        validated_data.pop("password1")
        return User.objects.create_user(**validated_data)


# Serializer for managing user profile info
class ProfileSerializer(serializers.ModelSerializer):
    """Profile serializer to manage extra user info"""

    languages = serializers.SlugRelatedField(
        many=True, slug_field="name", queryset=Languages.objects.all()
    )
    frameworks = serializers.SlugRelatedField(
        many=True, slug_field="name", queryset=Frameworks.objects.all()
    )
    otp_code = serializers.CharField(
        max_length=4,
        validators=[FieldValidators.xss_validator, FieldValidators.otp_validator],
        write_only=True,
        required=False,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "otp_code",
            "first_name",
            "last_name",
            "email",
            "avatar",
            "job_field",
            "languages",
            "frameworks",
        ]
        read_only_fields = [
            "id",
        ]

    def validate(self, attrs):
        if attrs.get("phone") != None:
            try:
                db_phone = User.objects.get(phone=attrs.get("phone"))
            except User.DoesNotExist:
                if attrs.get("otp_code") != None:
                    if cache.get(f"register:{attrs.get('phone')}") != None:
                        if attrs.get("otp_code") == cache.get(
                            f"register:{attrs.get('phone')}"
                        ):
                            cache.delete(f"register:{attrs.get('phone')}")
                            attrs.pop("otp_code", None)
                        else:
                            raise serializers.ValidationError(Errors.INVALID_OTP_CODE)
                    else:
                        raise serializers.ValidationError(Errors.INVALID_OTP_CODE)
                else:
                    raise serializers.ValidationError(Errors.OTP_BLANK)
            else:
                if attrs.get("phone") == db_phone.phone:
                    pass

        return super().validate(attrs)


# Serializer for changing user password
class ChangePasswordSerializer(serializers.Serializer):
    """Change password serializer"""

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    new_password1 = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs.get("new_password") != attrs.get("new_password1"):
            raise serializers.ValidationError(Errors.PASSWORD_MISMATCHED)
        try:
            validate_password(attrs.get("new_password"))
        except exceptions.ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})

        return super().validate(attrs)


# Serializer for resetting user password using OTP
class ResetPasswordSerializer(serializers.Serializer):
    """Reset password serializer"""

    phone = serializers.CharField(
        max_length=11,
        validators=[
            FieldValidators.iranian_phone_validator,
            FieldValidators.xss_validator,
        ],
    )
    otp_code = serializers.CharField(
        max_length=4,
        validators=[FieldValidators.xss_validator, FieldValidators.otp_validator],
    )
    new_password = serializers.CharField(required=True)
    new_password1 = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs.get("new_password") != attrs["new_password1"]:
            raise serializers.ValidationError(Errors.PASSWORD_MISMATCHED)
        try:
            validate_password(attrs.get("new_password"))
        except exceptions.ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
        return super().validate(attrs)


# Serializer for sending OTP
class OTPSendSerializer(serializers.Serializer):
    """Serializer for Send OTP"""

    OTP_TYPE_CHOICES = (
        ("register_otp", "Register OTP"),
        ("reset_password_otp", "Reset Password OTP"),
    )
    phone = serializers.CharField(
        max_length=11,
        validators=[
            FieldValidators.iranian_phone_validator,
            FieldValidators.xss_validator,
        ],
    )
    otp_type = serializers.ChoiceField(choices=OTP_TYPE_CHOICES, allow_null=False)

    class Meta:
        fields = [
            "phone",
        ]

    def set_cache(self):
        phone = self.validated_data["phone"]
        otp_type = self.validated_data["otp_type"]
        if otp_type == "register_otp":
            user_obj = User.objects.filter(phone=phone).exists()
            if not user_obj:
                if cache.get(f"register:{phone}") == None:
                    generate_otp = random.randint(1000, 9999)
                    cache.set(
                        f"register:{phone}", f"{generate_otp}", settings.OTP_CODE_TIME
                    )
                    if send_otp.delay(phone, generate_otp):
                        return {"detail": "ok"}, status.HTTP_200_OK
                    else:
                        return (
                            Errors.SMS_PANEL,
                            status.HTTP_502_BAD_GATEWAY,
                        )
                else:
                    return Errors.OTP_SPAM, status.HTTP_406_NOT_ACCEPTABLE
            else:
                return {
                    "detail": "The User Already Registered"
                }, status.HTTP_406_NOT_ACCEPTABLE
        elif otp_type == "reset_password_otp":
            get_object_or_404(User, phone=phone)
            if cache.get(f"reset_password:{phone}") == None:
                generate_otp = random.randint(1000, 9999)
                cache.set(
                    f"reset_password:{phone}",
                    f"{generate_otp}",
                    settings.OTP_CODE_TIME,
                )
                if send_otp.delay(phone, generate_otp):
                    return {"detail": "ok"}, status.HTTP_200_OK
                else:
                    return (
                        Errors.SMS_PANEL,
                        status.HTTP_502_BAD_GATEWAY,
                    )
            else:
                return Errors.OTP_SPAM, status.HTTP_406_NOT_ACCEPTABLE
