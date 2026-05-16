import re

from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import transaction
from rest_framework import serializers

from .models import UserProfile, Wallet


SIGNUP_VEHICLE_TYPE_MAP = {
    "sedan": "car",
    "bus": "bus",
    "truck": "truck",
    "van": "van",
}


class SignupSerializer(serializers.Serializer):
    fullName = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    nationalId = serializers.CharField(max_length=50)
    vehiclePlate = serializers.FileField(required=False, allow_null=True)
    licensePhoto = serializers.FileField(required=True)
    vehicleType = serializers.CharField(max_length=20)
    vehicleModel = serializers.CharField(max_length=120, required=False, allow_blank=True)
    vehicleColor = serializers.CharField(max_length=50, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    confirmPassword = serializers.CharField(write_only=True)
    otpCode = serializers.CharField(write_only=True)
    agreeToTerms = serializers.BooleanField()

    def validate_otpCode(self, value):
        code = str(value or "").strip()
        if not code:
            raise serializers.ValidationError("Enter the OTP code sent to your email.")
        return code

    def validate_agreeToTerms(self, value):
        if not value:
            raise serializers.ValidationError("You must accept the terms to register.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirmPassword"]:
            raise serializers.ValidationError({"confirmPassword": "Passwords do not match."})
        vtype = attrs["vehicleType"].lower()
        if vtype not in SIGNUP_VEHICLE_TYPE_MAP:
            raise serializers.ValidationError({"vehicleType": "Invalid vehicle type."})

        if not attrs.get("licensePhoto"):
            raise serializers.ValidationError(
                {"licensePhoto": "Upload a vehicle photo so we can read your plate with AI."}
            )

        return attrs

    def validate_phone(self, value):
        digits = re.sub(r"\D", "", value)
        if len(digits) < 10 or len(digits) > 15:
            raise serializers.ValidationError(
                "Enter a valid phone number (10–15 digits)."
            )
        return value.strip()

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value.strip()).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.strip().lower()

    def validate_nationalId(self, value):
        nid = value.strip()
        if not re.fullmatch(r"\d{14}", nid):
            raise serializers.ValidationError("National ID must be exactly 14 digits.")
        if UserProfile.objects.filter(national_id=nid).exists():
            raise serializers.ValidationError("This national ID is already registered.")
        return nid

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data["email"]
        password = validated_data["password"]
        full_name = validated_data["fullName"].strip()
        validated_data.pop("licensePhoto", None)
        validated_data.pop("vehiclePlate", None)
        vehicle_type = validated_data.pop("vehicleType")
        vehicle_model = (validated_data.pop("vehicleModel", None) or "").strip()[:120]
        vehicle_color = (validated_data.pop("vehicleColor", None) or "").strip()[:50]
        mapped_type = SIGNUP_VEHICLE_TYPE_MAP[vehicle_type.lower()]

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name[:150],
        )

        UserProfile.objects.create(
            user=user,
            national_id=validated_data["nationalId"],
            phone=validated_data["phone"].strip(),
        )
        Wallet.objects.create(user=user)

        user._signup_vehicle_type = mapped_type  # noqa: SLF001 — consumed by SignupView
        user._signup_vehicle_model = vehicle_model
        user._signup_vehicle_color = vehicle_color

        return user


class ProfileUpdateSerializer(serializers.Serializer):
    fullName = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=20, required=False)
    newPassword = serializers.CharField(
        write_only=True, min_length=8, required=False, allow_blank=True
    )
    currentPassword = serializers.CharField(write_only=True)

    def validate_phone(self, value):
        digits = re.sub(r"\D", "", value)
        if len(digits) < 10 or len(digits) > 15:
            raise serializers.ValidationError(
                "Enter a valid phone number (10–15 digits)."
            )
        return value.strip()

    def validate_email(self, value):
        user = self.context["request"].user
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("This email is already registered.")
        return email

    def validate(self, attrs):
        user = self.context["request"].user
        current = attrs.get("currentPassword") or ""
        if not user.check_password(current):
            raise serializers.ValidationError(
                {"currentPassword": "Current password is incorrect."}
            )
        new_pw = (attrs.get("newPassword") or "").strip()
        if new_pw:
            attrs["newPassword"] = new_pw
        else:
            attrs.pop("newPassword", None)

        # Do not require a "meaningful diff" here: the client may send the same
        # values after password verification, and optional-field handling can
        # omit keys from validated_data in edge cases, which incorrectly tripped
        # "Provide at least one field to update" while the password was valid.
        return attrs

    @transaction.atomic
    def save(self):
        user = self.context["request"].user
        data = self.validated_data
        profile = UserProfile.objects.select_for_update().get(user=user)

        if "fullName" in data:
            user.first_name = data["fullName"].strip()[:150]
        if "email" in data:
            user.email = data["email"]
            user.username = data["email"]
        if "phone" in data:
            profile.phone = data["phone"]
        if data.get("newPassword"):
            user.set_password(data["newPassword"])

        user.save()
        profile.save()
        return user
