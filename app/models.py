from django.utils import timezone
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from azure.storage.blob import BlobServiceClient
import logging
from urllib.parse import urlparse
from django.core.exceptions import ValidationError


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    content = models.TextField(
        blank=True,
        null=True,
    )
    date_posted = models.DateTimeField(auto_now_add=True)
    image = models.URLField(blank=True, null=True, max_length=1000)
    generated_prompt = models.TextField(blank=True, null=True)
    caption = models.TextField(blank=True, null=True)
    tags = models.JSONField(blank=True, null=True)
    is_public = models.BooleanField(default=False)

    current_owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="owned_posts",
        help_text="작품의 현재 소유자",
    )
    original_creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_posts",
        help_text="작품의 원작자",
    )
    ownership_history = models.JSONField(
        default=list,
        help_text="소유권 이전 기록 [{'owner': user_id, 'date': timestamp, 'type': 'auction/transfer}]",
    )

    @property
    def is_on_auction(self):
        """현재 경매 중인지 확인"""
        try:
            return self.auction is not None and self.auction.status == AuctionStatus.ACTIVE and self.auction.end_time > timezone.now()
        except Auction.DoesNotExist:
            return False

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        if self.image:
            try:
                blob_service_client = BlobServiceClient.from_connection_string(
                    settings.AZURE_CONNECTION_STRING
                )
                container_client = blob_service_client.get_container_client(
                    settings.CONTAINER_NAME
                )

                blob_name = urlparse(self.image).path.split("/")[-1]

                container_client.delete_blob(blob_name)
                logging.info(f"Blob {blob_name} deleted successfully")

            except Exception as e:
                logging.error(f"Error deleting blob: {str(e)}")

        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.original_creator = self.user
            self.current_owner = self.user
            self.ownership_history.append(
                {
                    "owner": self.user.id,
                    "date": timezone.now().isoformat(),
                    "type": "creation",
                }
            )
        super().save(*args, **kwargs)

        if self.image and not isinstance(self.image, str):
            self.image_url = self.image.url

    @property
    def author_nickname(self):
        return (
            self.user.profile.nickname
            if hasattr(self.user, "profile")
            else self.user.username
        )

    @property
    def likes_count(self):
        return self.likes.count()

    @property
    def is_popular(self):
        return self.likes_count >= 10

    def transfer_ownership(self, new_owner, transfer_type="auction"):
        """소유권 이전"""
        self.current_owner = new_owner
        self.ownership_history.append(
            {
                "owner": new_owner.id,
                "date": timezone.now().isoformat(),
                "type": transfer_type,
            }
        )
        self.save()


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment by {self.author} on {self.post}"

    @property
    def author_nickname(self):
        return (
            self.author.profile.nickname
            if hasattr(self.author, "profile")
            else self.author.username
        )


class AIGeneration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    prompt = models.TextField()
    generated_prompt = models.TextField()
    image_url = models.URLField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s image - {self.created_at}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "AI 생성 이미지"
        verbose_name_plural = "AI 생성 이미지들"


class TagUsage(models.Model):
    tag = models.CharField(max_length=100, unique=True)
    count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.tag} : {self.count}"


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")


class AuctionStatus(models.TextChoices):
    PENDING = "pending", "대기중"
    ACTIVE = "active", "진행중"
    ENDED = "ended", "종료"
    CANCELLED = "cancelled", "취소됨"


class Auction(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name="auction")
    seller = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="auctions_selling"
    )
    start_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(
        max_length=20, choices=AuctionStatus.choices, default=AuctionStatus.PENDING
    )
    winner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auctions_won",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"작품: {self.post.title}"

    @property
    def is_active(self):
        now = timezone.now()
        return (
            self.status == AuctionStatus.ACTIVE
            and self.start_time <= now <= self.end_time
        )

    def can_bid(self, user):
        return (
            user != self.seller
            and self.is_active
            and self.status == AuctionStatus.ACTIVE
        )

    def clean(self):
        if self.post.is_on_auction:
            raise ValidationError("이미 경매 중인 작품입니다.")
        if self.seller != self.post.current_owner:
            raise ValidationError("현재 소유자만 경매를 등록할 수 있습니다.")

    def finalise_auction(self):
        """경매 종료 및 소유권 이전"""
        if self.status == AuctionStatus.ACTIVE and self.winner:
            self.status = AuctionStatus.ENDED
            self.post.transfer_ownership(self.winner, "auction")
            self.save()


class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name="bids")
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-amount"]

    def __str__(self):
        return f"{self.auction} 작품에 대해 {self.amount} 가격이 입찰되었습니다."

    def save(self, *args, **kwargs):
        if self.amount > self.auction.current_price:
            self.auction.current_price = self.amount
            self.auction.save()
            super().save(*args, **kwargs)
