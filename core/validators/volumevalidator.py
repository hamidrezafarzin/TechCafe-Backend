from django.core.exceptions import ValidationError


class VolumeValidator:
    def validate_avatar_size(value):
        limit_mb = 5
        if value.size > limit_mb * 1024 * 1024:  # Convert MB to bytes
            raise ValidationError(f"Avatar size should be {limit_mb} MB or less.")
