from rest_framework import serializers
from gathering.models import Gathering, GatheringUser, Photo, Discount
from accounts.models import User
from utils.constants import Errors
from django.urls import reverse
from gathering.services.bank_gateway import Gateway
from rest_framework import status
from django.utils import timezone
import datetime

# Serializer for gathering details (read-only)
class GatheringSerializer(serializers.ModelSerializer):
    absolute_url = serializers.SerializerMethodField(method_name="get_abs_url")
    snippet = serializers.ReadOnlyField(source="get_snippet")
    presenter = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field=("fullname"),
    )

    class Meta:
        model = Gathering
        fields = [
            "id",
            "title",
            "description",
            "poster",
            "snippet",
            "absolute_url",
            "presenter",
            "address",
            "price",
            "date",
            "max_seats",
            "is_held",
            "is_occupied",
        ]

    # Method to get the absolute URL for a gathering
    def get_abs_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.pk)

    # Customize the representation of a gathering
    def to_representation(self, instance):
        request = self.context.get("request")
        rep = super().to_representation(instance)
        if instance.price == 0:
            filled_seats = GatheringUser.objects.filter(gathering=instance.id).count()
        else:
            filled_seats = GatheringUser.objects.filter(
                gathering=instance.id, is_paid=True
            ).count()
        if request.parser_context.get("kwargs").get("pk"):
            rep.pop("snippet", None)
            rep.pop("absolute_url", None)
        else:
            rep.pop("description", None)
        rep["filled_seats"] = filled_seats
        rep["empty_seats"] = instance.max_seats - filled_seats
        return rep

# Serializer for editing gathering details
class GatheringEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gathering
        fields = [
            "id",
            "title",
            "description",
            "poster",
            "presenter",
            "address",
            "price",
            "date",
            "max_seats",
            "is_held",
            "is_occupied",
        ]

# Serializer for user data (read-only)
class UserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone", "first_name", "last_name", "fullname", "is_ban"]
        read_only_fields = [
            "id",
            "phone",
            "first_name",
            "last_name",
            "fullname",
            "is_ban",
        ]

# Serializer for creating gathering registrations
class GatheringRegistrationCreateSerializer(serializers.ModelSerializer):
    discount_code = serializers.CharField(write_only=True, required=False)
    user = UserDataSerializer(read_only=True)

    class Meta:
        model = GatheringUser
        fields = [
            "id",
            "gathering",
            "user",
            "is_paid",
            "discount_code",
        ]
        read_only_fields = ["id", "is_paid", "user"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["detail"] = "successfully added to List"
        return rep

    def validate(self, attrs):
        request = self.context.get("request")

        # Check if the user is already registered for the gathering
        if GatheringUser.objects.filter(
            gathering=attrs.get("gathering"), user=request.user
        ).exists():
            raise serializers.ValidationError(Errors.ALREADY_REGISTERED)

        # Calculate the number of filled seats
        if attrs.get("gathering").price == 0:
            filled_seats = GatheringUser.objects.filter(
                gathering=attrs.get("gathering").id
            ).count()
        else:
            filled_seats = GatheringUser.objects.filter(
                gathering=attrs.get("gathering").id, is_paid=True
            ).count()

        # Validate the discount code
        if attrs.get("discount_code", None):
            try:
                discount_obj = Discount.objects.get(
                    code=attrs.get("discount_code"), gathering=attrs.get("gathering")
                )
            except Discount.DoesNotExist:
                attrs.pop("discount_code", None)
                raise serializers.ValidationError(Errors.INVALID_DISCOUNT_CODE)
            else:
                attrs.pop("discount_code", None)
                attrs["discount"] = discount_obj

        # Validate event details for registration
        if (
            attrs.get("gathering").is_held == False
            and attrs.get("gathering").is_occupied == False
            and int(attrs.get("gathering").max_seats) > filled_seats
            and request.user.is_ban == False
        ):
            pass
        elif attrs.get("gathering").is_held == True:
            raise serializers.ValidationError(Errors.GATHERING_HELD)
        elif attrs.get("gathering").is_occupied == True:
            raise serializers.ValidationError(Errors.Full_capacity)
        elif int(attrs.get("gathering").max_seats) <= filled_seats:
            raise serializers.ValidationError(Errors.Full_capacity)
        elif request.user.is_ban == True:
            raise serializers.ValidationError(Errors.USER_BANNED)
        return super().validate(attrs)

    def create(self, validated_data):
        validated_data["user"] = self.context.get("request").user
        return super().create(validated_data)

# Serializer for canceling gathering registrations
class GatheringRegistrationDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = GatheringUser
        fields = [
            "id",
            "gathering",
            "user",
        ]
        read_only_fields = ["id", "gathering", "user"]

    def validate(self, attrs):
        if self.instance.gathering.is_held == True:
            raise serializers.ValidationError(Errors.GATHERING_HELD)
        elif (
            timezone.localtime() + datetime.timedelta(days=2)
            > self.instance.gathering.date
        ):
            raise serializers.ValidationError(Errors.TIME_CANCELLATION)
        return super().validate(attrs)

    def delete(self):
        obj = self.instance
        obj.delete()
        return {"detail": "successfully cancelled"}, status.HTTP_204_NO_CONTENT

# Serializer for gathering registrations (read-only)
class GatheringRegistrationSerializer(serializers.ModelSerializer):
    user = UserDataSerializer(read_only=True)

    class Meta:
        model = GatheringUser
        fields = [
            "id",
            "gathering",
            "user",
            "is_paid",
        ]
        read_only_fields = ["id", "is_paid"]

    def to_representation(self, instance):
        if instance.gathering.price == 0:
            filled_seats = GatheringUser.objects.filter(
                gathering=instance.gathering.id
            ).count()
        else:
            filled_seats = GatheringUser.objects.filter(
                gathering=instance.gathering.id, is_paid=True
            ).count()
        rep = super().to_representation(instance)
        if instance.gathering.price == 0 or instance.is_paid:
            rep["gathering"] = {
                "id": instance.gathering.id,
                "title": instance.gathering.title,
                "price": instance.gathering.price,
                "max_seats": instance.gathering.max_seats,
                "filled_seats": filled_seats,
                "link": instance.gathering.link,
                "uuid": instance.uuid,
                "uuid_url": reverse(
                    "gathering:api-v1:check_in", kwargs={"get_uuid": instance.uuid}
                ),
                "check_in": instance.check_in,
            }
        elif instance.gathering.price != 0 and instance.is_paid == False:
            rep["gathering"] = {
                "id": instance.gathering.id,
                "title": instance.gathering.title,
                "price": instance.gathering.price,
                "max_seats": instance.gathering.max_seats,
                "filled_seats": filled_seats,
            }
            rep["payment_gateway"] = "Activate"
        return rep

# Serializer for gathering photos (read-only)
class GatheringImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ["gathering", "image"]

# Serializer for checking in users at gatherings
class GatheringCheckInSerializer(serializers.ModelSerializer):
    class Meta:
        model = GatheringUser
        fields = ["uuid", "check_in"]
        read_only_fields = ["uuid", "check_in"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["accept"] = True
        return rep

    def validate(self, attrs):
        if not self.instance.gathering.is_held and not self.instance.check_in:
            pass
        elif self.instance.gathering.is_held:
            raise serializers.ValidationError(Errors.GATHERING_HELD)
        elif self.instance.check_in:
            raise serializers.ValidationError(Errors.ALREADY_ENTERED)
        return super().validate(attrs)

    def update(self, instance, validated_data):
        instance.check_in = True
        return super().update(instance, validated_data)

# Serializer for gathering discount details (read-only)
class DiscountSerializer(serializers.ModelSerializer):
    gathering = serializers.SerializerMethodField()

    class Meta:
        model = Discount
        fields = ["code", "gathering", "discount_percentage", "status"]

    def get_gathering(self, instance):
        return {
            "id": instance.gathering.id,
            "title": instance.gathering.title,
            "price": instance.gathering.price,
        }

# Serializer for processing payments through a gateway
class GatheringGoGatewaySerializer(serializers.ModelSerializer):
    class Meta:
        model = GatheringUser
        fields = [
            "id",
        ]
        read_only_fields = [
            "id",
        ]

    def validate(self, attrs):
        request = self.context.get("request")
        if self.instance.gathering.price != 0:
            filled_seats = GatheringUser.objects.filter(
                gathering=self.instance.gathering.id
            ).count()
        else:
            raise serializers.ValidationError(Errors.EVENT_IS_FREE)

        if (
            int(self.instance.gathering.max_seats) > filled_seats
            and not self.instance.gathering.is_held
            and not self.instance.gathering.is_occupied
            and not self.instance.is_paid
            and not self.instance.user.is_ban
        ):
            pass
        elif (
            int(self.instance.gathering.max_seats) <= filled_seats
            or self.instance.gathering.is_occupied
        ):
            raise serializers.ValidationError(Errors.Full_capacity)
        elif self.instance.gathering.is_held:
            raise serializers.ValidationError(Errors.GATHERING_HELD)
        elif self.instance.is_paid:
            raise serializers.ValidationError(Errors.ALREADY_IS_PAID_TRUE)
        elif self.instance.user.is_ban:
            raise serializers.ValidationError(Errors.USER_BANNED)

        if self.instance.discount != None:
            attrs["final_price"] = self.instance.gathering.price - (
                (
                    self.instance.gathering.price
                    * self.instance.discount.discount_percentage
                )
                / 100
            )
        else:
            attrs["final_price"] = self.instance.gathering.price

        self.final_price = attrs["final_price"]
        return super().validate(attrs)

    def bank_initialization(self):
        if self.final_price <= 0:
            obj = GatheringUser.objects.get(pk=self.context["pk"])
            obj.is_paid = True
            obj.save()
            return {
                "detail": "The user was successfully registered in the event"
            }, status.HTTP_201_CREATED
        else:
            data = Gateway(request=self.context["request"]).go_to_gateway_view(
                amount=self.final_price, object_id=self.context["pk"]
            )
            if data["success"] == True:
                return data["context"], status.HTTP_200_OK
            elif data["success"] == False and data["object_DoesNotExist"] == False:
                return {"detail": "Error"}, status.HTTP_502_BAD_GATEWAY
            elif data["success"] == False and data["object_DoesNotExist"]:
                return {"detail": "Not found."}, status.HTTP_404_NOT_FOUND
