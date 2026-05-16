from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsAdminUser

from .gate_service import (
    PlateBelongsToOtherUser,
    PlateNotDetected,
    canonical_plate,
    find_vehicle_by_plate,
)
from .models import PlateScan
from .services import (
    create_plate_scan,
    decode_bytes_to_bgr,
    read_upload_bytes,
    run_vision_pipeline,
    scan_to_dict,
)


def _resolve_owner_user(request):
    """Staff must pass owner_user_id; returns (user, error_response)."""
    raw = request.data.get("owner_user_id") or request.data.get("user_id")
    if not raw:
        return None, Response(
            {"detail": "Select a user account (owner_user_id)."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        owner_id = int(raw)
    except (TypeError, ValueError):
        return None, Response(
            {"detail": "Invalid owner_user_id."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    owner = User.objects.filter(pk=owner_id, is_active=True, is_staff=False).first()
    if not owner:
        return None, Response(
            {"detail": "User account not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    return owner, None


class UserPlateScanListView(APIView):
    """Users can view their own scan history (read-only)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_staff:
            return Response(
                {"detail": "Use the admin plate scan portal to register vehicles."},
                status=status.HTTP_403_FORBIDDEN,
            )
        qs = PlateScan.objects.filter(user=request.user).select_related("vehicle")[:20]
        return Response([scan_to_dict(s, request) for s in qs])


class AdminPlateScanView(APIView):
    """Admin: register vehicle + gate pass for a selected user account."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        qs = PlateScan.objects.select_related("vehicle", "user").order_by("-created_at")
        user_id = request.query_params.get("user_id") or request.query_params.get("owner_user_id")
        if user_id:
            qs = qs.filter(user_id=user_id)
        return Response([scan_to_dict(s, request) for s in qs[:50]])

    def post(self, request):
        image = request.FILES.get("image") or request.FILES.get("file")
        if not image:
            return Response(
                {"detail": "Upload a vehicle image (field name: image or file)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        owner = None
        if request.data.get("owner_user_id") or request.data.get("user_id"):
            owner, err = _resolve_owner_user(request)
            if err:
                return err
        else:
            raw_bytes = read_upload_bytes(image)
            bgr = decode_bytes_to_bgr(raw_bytes) if raw_bytes else None
            if bgr is None:
                return Response(
                    {
                        "detail": "Could not read the uploaded image. Use JPG or PNG and try again."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            result = run_vision_pipeline(bgr)
            detected_plate = canonical_plate(result.get("plate_text") or "")
            if not detected_plate:
                return Response(
                    {
                        "detail": "Could not detect a license plate in the image.",
                        "code": "plate_not_detected",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            existing_vehicle = find_vehicle_by_plate(detected_plate)
            if not existing_vehicle:
                return Response(
                    {
                        "detail": (
                            "Could not automatically map this plate to an existing user. "
                            "Please select a user or register the vehicle first."
                        ),
                        "code": "owner_not_found",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            owner = existing_vehicle.user

        signup_model = (request.data.get("vehicle_model") or request.data.get("vehicleModel") or "")[:120]
        signup_color = (request.data.get("vehicle_color") or request.data.get("vehicleColor") or "")[:50]
        default_type = request.data.get("vehicle_type") or request.data.get("vehicleType") or "car"
        type_map = {
            "private-car": "car",
            "sedan": "car",
            "minibus": "minibus",
            "bus": "bus",
            "truck": "truck",
            "van": "van",
        }
        default_type = type_map.get(str(default_type).lower(), default_type)
        if default_type not in ("car", "truck", "bus", "van", "minibus", "motorcycle"):
            default_type = "car"

        try:
            scan = create_plate_scan(
                owner,
                image,
                source=PlateScan.SOURCE_ADMIN,
                signup_vehicle_type=default_type,
                signup_model=signup_model,
                signup_color=signup_color,
                record_gate_pass_trip=True,
            )
        except PlateBelongsToOtherUser:
            return Response(
                {
                    "detail": "This plate is already registered to another user account.",
                    "code": "plate_owned_by_other",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except PlateNotDetected:
            return Response(
                {
                    "detail": "Could not read a license plate from this image.",
                    "code": "plate_not_detected",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = scan_to_dict(scan, request)
        if not scan.models_ready and scan.error_message:
            return Response(payload, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(payload, status=status.HTTP_201_CREATED)


class PlateScanDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if request.user.is_staff:
            scan = PlateScan.objects.filter(pk=pk).select_related("vehicle", "user").first()
        else:
            scan = PlateScan.objects.filter(user=request.user, pk=pk).first()
        if not scan:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(scan_to_dict(scan, request))
