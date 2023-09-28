"""core URL Configuration
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from decouple import config
from core.views import admin_meme
from azbankgateways.urls import az_bank_gateways_urls

schema_view = get_schema_view(
    openapi.Info(
        title="Tech Cafe Rest API",
        default_version="v 1.0.0",
        description="Tech Cafe Rest API Backend Service",
        # terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="hamidfarzin1382@gmail.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.IsAdminUser,),
)

urlpatterns = [
    # admin panel
    path(f"{config('ADMIN_URL', default='test')}/", admin.site.urls),
    # admin panel meme
    path("admin/", admin_meme),
    # accounts app
    path("accounts/", include("accounts.urls")),
    # gathering app
    path("gathering/", include("gathering.urls")),
    # api authentication
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    # api docs
    path(
        "swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    # silk
    path(
        f"{config('SILK_URL', default='silk')}/", include("silk.urls", namespace="silk")
    ),
    path("bankgateways/", az_bank_gateways_urls()),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
