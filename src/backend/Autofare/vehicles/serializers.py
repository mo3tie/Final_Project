import re

from rest_framework import serializers

from .models import Vehicle


ADD_VEHICLE_TYPE_MAP = {
    "private-car": "car",
    "minibus": "minibus",
    "bus": "bus",
    "truck": "truck",
}


class VehicleSerializer(serializers.ModelSerializer):
    type_label = serializers.SerializerMethodField()
    plate = serializers.CharField(source="license_plate", read_only=True)

    class Meta:
        model = Vehicle
        fields = (
            "id",
            "plate",
            "vehicle_type",
            "type_label",
            "model_label",
            "color",
            "is_active",
        )
        read_only_fields = ("id", "vehicle_type", "plate")

    def get_type_label(self, obj):
        return dict(Vehicle.VEHICLE_TYPES).get(obj.vehicle_type, obj.vehicle_type)


class VehicleCreateSerializer(serializers.ModelSerializer):
    vehicleType = serializers.ChoiceField(
        choices=list(ADD_VEHICLE_TYPE_MAP.keys()),
        write_only=True,
    )
    licensePlate = serializers.CharField(max_length=20, write_only=True)
    vehicleModel = serializers.CharField(
        max_length=120, required=False, allow_blank=True, write_only=True
    )
    vehicleColor = serializers.CharField(
        max_length=50, required=False, allow_blank=True, write_only=True
    )

    class Meta:
        model = Vehicle
        fields = ("vehicleType", "licensePlate", "vehicleModel", "vehicleColor")

    def validate_licensePlate(self, value):
        plate = value.strip().upper()
        if len(plate) < 3:
            raise serializers.ValidationError("Enter a valid license plate.")
        if not re.match(r"^[\w\s\-]+$", plate):
            raise serializers.ValidationError("Plate contains invalid characters.")
        if Vehicle.objects.filter(license_plate__iexact=plate).exists():
            raise serializers.ValidationError("This license plate is already registered.")
        return plate

    def create(self, validated_data):
        user = self.context["request"].user
        vt = ADD_VEHICLE_TYPE_MAP[validated_data["vehicleType"]]
        model_label = (validated_data.get("vehicleModel") or "").strip()[:120]
        color = (validated_data.get("vehicleColor") or "").strip()[:50]
        return Vehicle.objects.create(
            user=user,
            vehicle_type=vt,
            license_plate=validated_data["licensePlate"],
            model_label=model_label,
            color=color,
        )


class VehiclePatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ("is_active",)
