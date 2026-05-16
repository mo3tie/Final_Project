import logging
import random

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from ai.gate_service import PlateBelongsToOtherUser, PlateNotDetected
from ai.models import PlateScan
from ai.services import create_plate_scan, scan_to_dict

from .me_utils import build_me_payload
from .serializers import ProfileUpdateSerializer, SignupSerializer


def _display_name(user: User) -> str:
    full = (user.get_full_name() or "").strip()
    if full:
        return full
    if user.first_name:
        return user.first_name
    return user.email or user.username


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        password = request.data.get("password") or ""
        role = (request.data.get("role") or "user").lower()

        if not email or not password:
            return Response(
                {"non_field_errors": ["Email and password are required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(email__iexact=email).first()
        if user is None or not user.check_password(password):
            return Response(
                {"non_field_errors": ["Invalid email or password."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if role == "admin" and not user.is_staff:
            return Response(
                {"non_field_errors": ["You do not have administrator access."]},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "name": _display_name(user),
            },
            status=status.HTTP_200_OK,
        )


class SignupView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        license_photo = request.FILES.get("licensePhoto")
        if not license_photo:
            return Response(
                {"licensePhoto": ["Vehicle photo is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()
        plate_scan_payload = None
        accepted_plate = ""

        try:
            scan = create_plate_scan(
                user,
                license_photo,
                source=PlateScan.SOURCE_SIGNUP,
                signup_vehicle_type=getattr(user, "_signup_vehicle_type", "car"),
                signup_model=getattr(user, "_signup_vehicle_model", ""),
                signup_color=getattr(user, "_signup_vehicle_color", ""),
                record_gate_pass_trip=False,
            )
            plate_scan_payload = scan_to_dict(scan, request)
            accepted_plate = scan.detected_plate_text or (
                scan.vehicle.license_plate if scan.vehicle else ""
            )
        except PlateBelongsToOtherUser:
            transaction.set_rollback(True)
            return Response(
                {
                    "licensePhoto": [
                        "This plate is already registered to another account."
                    ],
                    "code": "plate_owned_by_other",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PlateNotDetected:
            transaction.set_rollback(True)
            return Response(
                {
                    "licensePhoto": [
                        "Could not read a license plate from your photo. Try a clearer image."
                    ],
                    "code": "plate_not_detected",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            logging.getLogger(__name__).exception("signup plate scan failed")
            transaction.set_rollback(True)
            return Response(
                {
                    "licensePhoto": [
                        "AI plate scan failed. Check that models are installed on the server."
                    ],
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        refresh = RefreshToken.for_user(user)
        user_data = build_me_payload(user, request)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "name": _display_name(user),
                "accepted_plate": accepted_plate,
                "plate_scan": plate_scan_payload,
                **user_data,
            },
            status=status.HTTP_201_CREATED,
        )


class SendSignupOtpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        if not email:
            return Response(
                {"email": ["Enter a valid email address."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email__iexact=email).exists():
            return Response(
                {"email": ["An account with this email already exists."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp_code = f"{random.randint(100000, 999999):06d}"
        cache_key = f"signup_otp:{email}"
        cache.set(cache_key, otp_code, 600)

        subject = "Your signup OTP code"
        message = (
            f"Your signup verification code is: {otp_code}\n\n"
            "Enter this code in the signup form to complete registration."
        )
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
        if not from_email:
            from_email = "noreply@example.com"

        try:
            send_mail(
                subject,
                message,
                from_email,
                [email],
                fail_silently=False,
            )
        except Exception:
            logging.getLogger(__name__).exception("Failed to send signup OTP email")
            return Response(
                {
                    "detail": (
                        "Unable to send the OTP email right now. Check mail settings or try again later."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {"detail": "OTP code sent to your email."},
            status=status.HTTP_200_OK,
        )


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(build_me_payload(request.user, request))

    def patch(self, request):
        ser = ProfileUpdateSerializer(
            data=request.data, context={"request": request}
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(build_me_payload(request.user, request))
