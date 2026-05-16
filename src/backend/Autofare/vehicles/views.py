from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Vehicle
from .serializers import VehicleCreateSerializer, VehiclePatchSerializer, VehicleSerializer


class VehicleListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Vehicle.objects.filter(user=self.request.user).order_by("id")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return VehicleCreateSerializer
        return VehicleSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(VehicleSerializer(instance).data, status=201)


class VehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return Vehicle.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return VehiclePatchSerializer
        return VehicleSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        plate = instance.license_plate
        self.perform_destroy(instance)
        return Response(
            {"detail": "Vehicle removed.", "id": kwargs.get("pk"), "plate": plate},
            status=status.HTTP_200_OK,
        )
