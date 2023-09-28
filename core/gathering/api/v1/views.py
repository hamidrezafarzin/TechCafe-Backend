from gathering.api.v1.serializers import (
    GatheringSerializer,
    GatheringEditSerializer,
    GatheringRegistrationSerializer,
    GatheringImageSerializer,
    DiscountSerializer,
    GatheringGoGatewaySerializer,
    GatheringCheckInSerializer,
    GatheringRegistrationCreateSerializer,
    GatheringRegistrationDeleteSerializer,
)
from gathering.models import Gathering, GatheringUser, Photo, Discount
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework import filters
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone
import datetime
from django.core.exceptions import ValidationError
from utils.constants import Errors
from rest_framework import generics
from rest_framework.views import APIView
from gathering.services.bank_gateway import Gateway

# ViewSet for managing gathering CRUD operations (staff only)
class GatheringEditModelViewSet(viewsets.ModelViewSet):
    """CRUD options for managing gatherings (staff only)"""

    permission_classes = [IsAdminUser]
    serializer_class = GatheringEditSerializer
    queryset = Gathering.objects.all()

# ViewSet for retrieving gathering details and filtering/searching
class GatheringModelViewSet(viewsets.ReadOnlyModelViewSet):
    """All users can view event details, filter by date, and search for events."""

    permission_classes = [AllowAny]
    serializer_class = GatheringSerializer
    queryset = Gathering.objects.all()
    lookup_field = "pk"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title"]
    ordering_fields = ["date", "is_held", "is_occupied"]

# ViewSet for validating discount codes
class DiscountModelViewSet(viewsets.ReadOnlyModelViewSet):
    """Validation for discount codes"""

    permission_classes = [AllowAny]
    serializer_class = DiscountSerializer
    queryset = Discount.objects.filter(status=True)
    lookup_field = "code"
    lookup_url_kwarg = "get_discount"

# ViewSet for gathering registrations (user registration for events)
class GatheringRegistrationModelViewSet(viewsets.ModelViewSet):
    """
    Users can register for events in this class, but they must be logged in to register.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self, pk=None):
        """
        The get_queryset function allows us to filter the data received from the database based on our needs.
        """
        if self.action == "list":
            queryset = GatheringUser.objects.filter(user=pk)
        elif self.action == "destroy":
            queryset = get_object_or_404(GatheringUser, id=pk)
        elif self.action == "retrieve":
            queryset = GatheringUser.objects.filter(user=self.request.user)
        return queryset

    def get_serializer_class(self, *args, **kwargs):
        if self.action == "create":
            return GatheringRegistrationCreateSerializer
        elif self.action == "list" or self.action == "retrieve":
            return GatheringRegistrationSerializer
        elif self.action == "destroy":
            return GatheringRegistrationDeleteSerializer

    def list(self, request):
        """Get the list of events registered by the user."""
        serializer = self.serializer_class(
            self.get_queryset(pk=request.user), many=True
        )
        return Response(serializer.data)

    def create(self, request):
        """
        If the method is POST, we create an object for the user in a custom table.
        If the serializer is valid, we return "successfully added to list."
        """
        serializer = self.get_serializer(
            data=request.data, many=False, context={"request": self.request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk):
        serializer = self.get_serializer(
            data=request.data,
            instance=self.get_queryset(pk=pk),
            context={"request": self.request, "pk": pk},
        )
        serializer.is_valid(raise_exception=True)
        detail, status = serializer.delete()
        return Response(detail, status)

# ViewSet for checking in users at events (staff only)
class GatheringCheckInModelViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = GatheringCheckInSerializer

    def get_queryset(self, get_uuid=None):
        if self.action == "retrieve":
            try:
                queryset = get_object_or_404(GatheringUser, uuid=get_uuid)
            except ValidationError:
                queryset = False
        return queryset

    def retrieve(self, request, get_uuid, *args, **kwargs):
        query = self.get_queryset(get_uuid=get_uuid)
        if query:
            serializer = self.serializer_class(
                data=request.data,
                instance=query,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        else:
            return Response(Errors.INVALID_UUID, status=status.HTTP_406_NOT_ACCEPTABLE)

# ViewSet for gathering photos (staff only)
class GatheringImageModelViewSet(viewsets.ReadOnlyModelViewSet):
    """Gathering Photos (staff only)"""

    permission_classes = [AllowAny]
    serializer_class = GatheringImageSerializer
    queryset = Photo.objects.all()
    lookup_field = "pk"
    filter_backends = [filters.SearchFilter]
    search_fields = ["gathering__id"]

# API view for processing payments through a gateway
class GatheringGoGatewayApiView(generics.CreateAPIView):  # UpdateAPIView
    permission_classes = [IsAuthenticated]
    serializer_class = GatheringGoGatewaySerializer
    allowed_methods = ["POST", "OPTIONS"]

    def get_queryset(self, id=None):
        obj = get_object_or_404(GatheringUser, pk=id)
        return obj

    def post(self, request, pk, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            instance=self.get_queryset(id=pk),
            context={"request": self.request, "pk": pk},
        )
        serializer.is_valid(raise_exception=True)
        result, status = serializer.bank_initialization()
        return Response(result, status)

# API view for handling gateway callback
class GatheringGatewayCallbackApiView(APIView):
    def get(self, request):
        data = Gateway(request=request).callback_gateway_view()
        if data["success"] == True:
            return Response(data["context"], status=status.HTTP_200_OK)
        elif data["success"] == False and data["object_DoesNotExist"]:
            Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        elif data["success"] == False and data["object_DoesNotExist"] == False:
            return Response(
                {"detail": f"{data['error']}"}, status=status.HTTP_502_BAD_GATEWAY
            )
