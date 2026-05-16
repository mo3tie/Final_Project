import re
from datetime import date

from decimal import Decimal
from rest_framework import serializers


def luhn_valid(card_number: str) -> bool:
    digits = [int(c) for c in card_number if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


class WalletRechargeSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("1"))
    cardholder_name = serializers.CharField(max_length=120)
    card_number = serializers.CharField(max_length=19)
    expiry_date = serializers.CharField(max_length=5)
    cvv = serializers.CharField(max_length=4)
    billing_address = serializers.CharField(max_length=500)

    def validate_cardholder_name(self, value):
        name = " ".join(value.split())
        if len(name) < 3:
            raise serializers.ValidationError("Enter the full name as shown on the card.")
        if not re.match(r"^[\w\s\-'.]+$", name, re.UNICODE):
            raise serializers.ValidationError("Cardholder name contains invalid characters.")
        return name

    def validate_card_number(self, value):
        raw = re.sub(r"\D", "", value)
        if len(raw) < 13 or len(raw) > 19:
            raise serializers.ValidationError("Card number must be between 13 and 19 digits.")
        if not luhn_valid(raw):
            raise serializers.ValidationError("Card number is not valid.")
        return raw

    def validate_expiry_date(self, value):
        m = re.match(r"^(\d{2})/(\d{2})$", value.strip())
        if not m:
            raise serializers.ValidationError("Use MM/YY format.")
        month, year = int(m.group(1)), int(m.group(2))
        if month < 1 or month > 12:
            raise serializers.ValidationError("Invalid month.")
        exp_year = 2000 + year if year < 100 else year
        today = date.today()
        if exp_year < today.year or (
            exp_year == today.year and month < today.month
        ):
            raise serializers.ValidationError("This card has expired.")
        return value.strip()

    def validate_cvv(self, value):
        raw = re.sub(r"\D", "", value)
        if len(raw) not in (3, 4):
            raise serializers.ValidationError("CVV must be 3 or 4 digits.")
        return raw

    def validate_billing_address(self, value):
        addr = value.strip()
        if len(addr) < 8:
            raise serializers.ValidationError("Enter a complete billing address.")
        return addr
