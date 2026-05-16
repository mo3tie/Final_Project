from django.db import models
from datetime import datetime, timedelta

class Violation(models.Model):
    vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.CASCADE)
    violation_date = models.DateTimeField(auto_now_add=True)
    violation_type = models.CharField(max_length=100)  # e.g., 'speeding', 'toll evasion'
    base_penalty = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)  # Base amount
    status = models.CharField(max_length=20, default='Unpaid')  # Paid, Unpaid

    def get_current_penalty(self):
        if self.status == 'Paid':
            return 0  # Penalty disappears once paid
        days_since = (datetime.now() - self.violation_date.replace(tzinfo=None)).days
        periods = days_since // 5  # Number of 5-day periods
        increase_percentage = 0.10  # 10% increase per 5 days
        multiplier = 1 + (periods * increase_percentage)
        return self.base_penalty * multiplier