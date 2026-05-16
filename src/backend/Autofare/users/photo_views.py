from pathlib import Path

from django.core.files.storage import default_storage
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .me_utils import build_me_payload
from .models import UserProfile

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 2 * 1024 * 1024


class ProfilePhotoView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        photo = request.FILES.get("photo")
        if not photo:
            return Response({"photo": ["No file was uploaded."]}, status=400)
        content_type = (photo.content_type or "").lower()
        if not content_type:
            ext = Path(photo.name or "").suffix.lower()
            ext_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".webp": "image/webp",
            }
            content_type = ext_map.get(ext, "")
        if content_type not in ALLOWED_TYPES:
            return Response(
                {"photo": ["Use a JPG, PNG, or WebP image."]},
                status=400,
            )
        if photo.size > MAX_BYTES:
            return Response(
                {"photo": ["Image must be 2 MB or smaller."]},
                status=400,
            )

        profile = UserProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response({"detail": "User profile not found."}, status=404)

        old_name = profile.photo.name if profile.photo else None
        profile.photo.save(photo.name, photo, save=True)
        if old_name and old_name != (profile.photo.name or ""):
            try:
                default_storage.delete(old_name)
            except OSError:
                pass

        return Response(build_me_payload(request.user, request), status=200)
