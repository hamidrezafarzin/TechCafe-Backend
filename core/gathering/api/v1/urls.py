from django.urls import path, include
from gathering.api.v1 import views
from rest_framework.routers import DefaultRouter

app_name = "api-v1"
router = DefaultRouter()

urlpatterns = [
    path(
        "event_register/<int:pk>/",
        views.GatheringRegistrationModelViewSet.as_view(
            {"get": "retrieve", "delete": "destroy"}
        ),
        name="event-register",
    ),
    path(
        "event_register/",
        views.GatheringRegistrationModelViewSet.as_view(
            {"get": "list", "post": "create"}
        ),
        name="my-event-list",
    ),
    path(
        "check_in/<str:get_uuid>/",
        views.GatheringCheckInModelViewSet.as_view({"get": "retrieve"}),
        name="check_in",
    ),
    path(
        "discount/check/<str:get_discount>/",
        views.DiscountModelViewSet.as_view({"get": "retrieve"}),
        name="discount-check",
    ),
    path(
        "event_register/go_to_gateway/<int:pk>/",
        views.GatheringGoGatewayApiView.as_view(),
        name="event-register-go-to-gateway",
    ),
    path(
        "event_register/gateway_callback/",
        views.GatheringGatewayCallbackApiView.as_view(),
        name="event-register-gateway-callback",
    ),
]


router.register(
    "manage-event", views.GatheringEditModelViewSet, basename="manage-event"
)
router.register("event", views.GatheringModelViewSet, basename="event")
router.register("images", views.GatheringImageModelViewSet, basename="images")
urlpatterns += router.urls
