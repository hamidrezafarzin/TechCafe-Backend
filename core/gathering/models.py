from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
import os
import uuid
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

# Define a model for gatherings.
class Gathering(models.Model):
    # Fields for gathering information.
    title = models.CharField(max_length=250, blank=False, null=False)
    description = models.TextField(blank=False, null=False)
    poster = models.ImageField(upload_to="events/posters")
    presenter = models.ManyToManyField("accounts.User", blank=True)
    address = models.TextField(null=True, blank=True)
    price = models.IntegerField(default=0, blank=False, null=False)
    link = models.URLField(null=True, blank=True)
    date = models.DateTimeField(auto_now=False)
    max_seats = models.PositiveSmallIntegerField(default=0, blank=False, null=False)
    is_online = models.BooleanField(default=False)
    is_held = models.BooleanField(default=False)
    is_occupied = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_snippet(self):
        return self.description[0:60] + "..."

    # Custom validation to ensure link field consistency.
    def clean(self):
        if self.is_online and not self.link:
            raise ValidationError(
                "When is_online is set to True, the link field cannot be blank."
            )
        elif not self.is_online and self.link:
            raise ValidationError(
                "When is_online is set to False, the link field cannot have a link."
            )

# Define a model for discounts associated with gatherings.
class Discount(models.Model):
    code = models.CharField(max_length=250, blank=False, null=False, unique=True)
    gathering = models.ForeignKey(
        Gathering, blank=False, null=False, on_delete=models.CASCADE
    )
    discount_percentage = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=False,
        null=False,
    )
    status = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code}"

# Define a model to associate users with gatherings and discounts.
class GatheringUser(models.Model):
    user = models.ForeignKey(to="accounts.User", on_delete=models.CASCADE)
    gathering = models.ForeignKey(Gathering, on_delete=models.CASCADE)
    discount = models.ForeignKey(
        Discount, blank=True, null=True, on_delete=models.SET_NULL
    )
    bank_gateway = models.ForeignKey(
        "azbankgateways.Bank", blank=True, null=True, on_delete=models.SET_NULL
    )
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    is_paid = models.BooleanField(default=False)
    check_in = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [
            "gathering",
            "user",
        ]

    def __str__(self):
        return f"{self.user}"

# Define a model for photos associated with gatherings.
class Photo(models.Model):
    gathering = models.ForeignKey(
        Gathering, related_name="gathering_img", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="events/gathering")

    def __str__(self):
        return f"{self.gathering.id}"

# Signal handler to delete associated image files when a Photo object is deleted.
@receiver(models.signals.post_delete, sender=Photo)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)

# Signal handler to delete unpaid users when a Gathering is held and has a non-zero price.
@receiver(post_save, sender=Gathering)
def delete_unpaid_users(sender, instance, created, **kwargs):
    if not created:
        if instance.is_held and instance.price != 0:
            try:
                GatheringUser.objects.filter(
                    gathering=instance.id, is_paid=False
                ).delete()
            except GatheringUser.DoesNotExist:
                pass

# Signal handler to deactivate discounts when a Gathering is held.
@receiver(post_save, sender=Gathering)
def deactivate_discounts_on_event_held(sender, instance, created, **kwargs):
    if not created:
        if instance.is_held:
            Discount.objects.filter(gathering=instance.id, status=True).update(
                status=False
            )
