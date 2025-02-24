from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=50)
    profile_image = models.URLField(blank=True, null=True)
    user_style = models.CharField(max_length=1000)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=10000)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}의 프로필"
    
class ChargeCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"충전코드: {self.code} (금액: {self.amount}원)"
    
class ChargeCodeUsage(models.Model):
    charge_code = models.ForeignKey(ChargeCode, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['charge_code', 'user']