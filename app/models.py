from django.utils import timezone
from django.db import models, transaction
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
        now = timezone.now()
        return (
            user != self.seller
            and self.start_time <= now <= self.end_time
            and self.status == AuctionStatus.ACTIVE
        )

    def clean(self):
        if self.post.is_on_auction:
            raise ValidationError("이미 경매 중인 작품입니다.")
        if self.seller != self.post.current_owner:
            raise ValidationError("현재 소유자만 경매를 등록할 수 있습니다.")

    @transaction.atomic
    def finalise_auction(self):
        """경매 종료 및 소유권 이전"""
        if self.status == AuctionStatus.ACTIVE and self.end_time <= timezone.now():
            if self.bids.exists() and self.winner:
                try:
                    self.seller.profile.balance += self.current_price
                    self.seller.profile.save()
                    
                    self.status = AuctionStatus.ENDED
                    self.save()
                    
                    previous_owner = self.post.current_owner
                    
                    self.post.transfer_ownership(self.winner, transfer_type="auction")
                    
                    logging.info(f"경매 #{self.id} 성공적으로 종료: 작품 '{self.post.title}'(#{self.post.id})가 {self.winner.username}에게 {self.current_price}원에 낙찰")
                    
                    return True, "경매가 성공적으로 종료되었습니다. 낙찰된 작품은 이제 귀하의 갤러리에서 확인하실 수 있습니다."
                
                except Exception as e:
                    logging.error(f"경매 종료 처리 중 오류 발생: {str(e)}")
                    return False, "경매 종료 처리 중 오류가 발생했습니다."
            else:
                self.status = AuctionStatus.CANCELLED
                self.save()
                return True, "입찰이 없어 경매가 취소되었습니다."
        
        return False, "종료할 수 없는 경매입니다."

    def place_bid(self, bidder, amount):
        if not self.can_bid(bidder):
            return False, "입찰 권한이 없습니다."
        
        if amount <= self.current_price:
            return False, "현재가보다 높은 금액을 입찰해주세요."
        
        if bidder.profile.balance < amount:
            return False, "잔액이 부족합니다."

        try:
            if self.bids.exists():
                last_bid = self.bids.first()
                last_bidder = last_bid.bidder
                last_bidder.profile.balance += last_bid.amount
                last_bidder.profile.save()

            bidder.profile.balance -= amount
            bidder.profile.save()

            Bid.objects.create(
                auction=self,
                bidder=bidder,
                amount=amount
            )

            self.current_price = amount
            self.winner = bidder
            self.save()

            logging.info(f"경매 #{self.id}: {bidder.username}님이 {amount}원 입찰")

            return True, "입찰이 완료되었습니다."

        except Exception as e:
            logging.error(f"입찰 처리 중 오류 발생: {str(e)}")
            return False, "입찰 처리 중 오류가 발생했습니다."
        
    @transaction.atomic
    def cancel(self):
        if self.status != AuctionStatus.ACTIVE:
            return False, "진행 중인 경매만 취소할 수 있습니다."

        try:
            for bid in self.bids.all():
                bid.bidder.profile.balance += bid.amount
                bid.bidder.profile.save()
                logging.info(f"경매 취소: 입찰자 {bid.bidder.username}에게 {bid.amount}원 환불")

            self.status = AuctionStatus.CANCELLED
            self.save()

            return True, "경매가 취소되었고 모든 입찰금액이 환불되었습니다."
        except Exception as e:
            logging.error(f"경매 취소 중 오류 발생: {str(e)}")
            return False, "경매 취소 처리 중 오류가 발생했습니다."


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

class FrameType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    price_addition = models.DecimalField(max_digits=10, decimal_places=0, default=5000) # 기본 프레임 추가 5,000원
    image_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
class ProductSize(models.Model):
    name = models.CharField(max_length=20)
    width = models.IntegerField()
    height = models.IntegerField()
    price_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    base_price = models.DecimalField(max_digits=10, decimal_places=0, default=29000) # M 사이즈 기준 29,000원
    is_active = models.BooleanField(default=True)

    def get_price(self):
        return self.base_price * self.price_multiplier

    def __str__(self):
        return f"{self.name} ({self.width}x{self.height}cm)"
    
class FinishType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    price_addition = models.DecimalField(max_digits=10, decimal_places=0, default=3000) # 기본 마감 추가 3,000원
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
class GoodsItem(models.Model):
    post = models.ForeignKey('Post', on_delete=models.CASCADE)
    frame_type = models.ForeignKey(FrameType, on_delete=models.SET_NULL, null=True)
    size = models.ForeignKey(ProductSize, on_delete=models.SET_NULL, null=True)
    finish_type = models.ForeignKey(FinishType, on_delete=models.SET_NULL, null=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=49.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def final_price(self):
        if not self.size:
            return 0
        
        price = self.size.get_price()
        if self.frame_type:
            price += self.frame_type.price_addition
        if self.finish_type:
            price += self.finish_type.price_addition
        return price
    
    def __str__(self):
        return f"Goods for {self.post.title}"