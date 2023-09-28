# from rest_framework.authtoken.views import ObtainAuthToken
from django.urls import path
from .views import (
    RegisterApiView,
    ProfileApiView,
    ChangePasswordAPIView,
    ResetPasswordAPIView,
    OTPSendAPIView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)


urlpatterns = [
    path("register/", RegisterApiView.as_view(), name="register"),
    # path("token/login", ObtainAuthToken.as_view(), name="token_obtain"),
    path("jwt/create/", TokenObtainPairView.as_view(), name="jwt_obtain_pair"),
    path("jwt/refresh/", TokenRefreshView.as_view(), name="jwt_refresh"),
    path("jwt/verify/", TokenVerifyView.as_view(), name="jwt_verify"),
    path("user/profile/", ProfileApiView.as_view(), name="profile"),
    path(
        "user/change-password/", ChangePasswordAPIView.as_view(), name="change_password"
    ),
    path("reset-password/", ResetPasswordAPIView.as_view(), name="change_password"),
    path("otp/send/", OTPSendAPIView.as_view(), name="otp_register_send"),
]
