from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .serializers import (
    ProfileSerializer,
    RegisterSerializer,
    ChangePasswordSerializer,
    ResetPasswordSerializer,
    OTPSendSerializer,
)
from accounts.models import User
import random
from django.core.cache import cache
from accounts.tasks import send_otp
from utils.constants import Errors
from django.conf import settings

# View to handle user registration.
class RegisterApiView(generics.CreateAPIView):
    """
    When a user registers, they send their registration data to this view. It uses the RegisterSerializer to validate and process the input data, creating a new user account in the process.
    """

    serializer_class = RegisterSerializer
    queryset = User.objects.all()

# View to retrieve and update user profiles.
class ProfileApiView(generics.RetrieveUpdateAPIView):

    """
    Authenticated users can access this view to retrieve or modify their profile details. It uses the ProfileSerializer for serialization and requires authentication (IsAuthenticated) for access.
    """
    queryset = User.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    # For not sending pk in URL:
    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, phone=self.request.user)
        return obj

# View to change a user's password.
class ChangePasswordAPIView(generics.GenericAPIView):
    """
    Authenticated users can use this view to update their passwords. It checks the old password for validation and updates the user's password with the new one. The ChangePasswordSerializer handles input validation.
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def get_object(self):
        obj = self.request.user
        return obj

    def put(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response(
                    {"old_password": ["Wrong password."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # set_password also hashes the password that the user will get
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            return Response(
                {"detail": "password changed successfully"}, status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# View to reset a user's password using OTP.
class ResetPasswordAPIView(generics.CreateAPIView):
    """
    Users who forget their passwords can request a reset through this view. It validates the OTP code and updates the password if the code is correct. Caching is used to store and validate OTP codes.
    """
    model = User
    serializer_class = ResetPasswordSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            if cache.get(f"reset_password:{serializer.data['phone']}") != None:
                if queryset := get_object_or_404(User, phone=serializer.data["phone"]):
                    if serializer.data["otp_code"] == cache.get(
                        f"reset_password:{serializer.data['phone']}"
                    ):
                        queryset.set_password(serializer.data.get("new_password"))
                        queryset.save()
                        cache.delete(f"reset_password:{serializer.data['phone']}")
                        return Response(
                            {"detail": "password successfully changed"},
                            status=status.HTTP_200_OK,
                        )
                    else:
                        return Response(
                            Errors.INVALID_OTP_CODE,
                            status=status.HTTP_406_NOT_ACCEPTABLE,
                        )
                else:
                    return Response(
                        {"detail": "user not found"}, status=status.HTTP_404_NOT_FOUND
                    )
            else:
                return Response(
                    Errors.INVALID_OTP_CODE,
                    status=status.HTTP_406_NOT_ACCEPTABLE,
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# View to send OTP for password reset.
class OTPSendAPIView(generics.CreateAPIView):
    serializer_class = OTPSendSerializer
    """
    Users can request OTP codes for actions like password reset by sending a request to this view. It generates and sends the OTP code to the user's phone number, utilizing the OTPSendSerializer. The code is stored in the cache for later verification.
    """

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        result, status = serializer.set_cache()
        return Response(result, status)
