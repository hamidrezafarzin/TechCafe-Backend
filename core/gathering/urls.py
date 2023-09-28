from django.urls import path, include

app_name = "gathering"

urlpatterns = [path("api/v1/", include("gathering.api.v1.urls"))]
