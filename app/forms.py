from django import forms
from .models import Post, Auction
from django.utils import timezone
from datetime import timedelta


class PostWithAIForm(forms.ModelForm):
    prompt = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 5}),
        required=False,
        help_text="AI 이미지 생성을 위한 프롬프트",
    )
    is_public = forms.BooleanField(
        required=False, initial=False, help_text="공개 갤러리에 공유하기"
    )

    class Meta:
        model = Post
        fields = ["title", "content", "is_public"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 5}),
        }


class PostEditForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "content"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 5}),
        }


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["content"]  # 필요한 다른 필드도 추가 가능
        widgets = {
            "content": forms.Textarea(attrs={"rows": 5}),
        }


class AuctionForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        label="경매 시작 시간",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        initial=timezone.now,
    )
    end_time = forms.DateTimeField(
        label="경매 종료 시간",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        initial=timezone.now() + timedelta(days=7),
    )
    start_price = forms.DecimalField(
        label="시작가",
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"placeholder": "시작가를 입력하세요."}),
    )

    class Meta:
        model = Auction
        fields = ["start_price", "start_time", "end_time"]

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time:
            if start_time < timezone.now():
                raise forms.ValidationError(
                    "경매 시작 시간은 현재 시간 이후여야 합니다."
                )
            if end_time <= start_time:
                raise forms.ValidationError(
                    "경매 종료 시간은 시작 시간 이후여야 합니다."
                )
            if end_time < timezone.now():
                raise forms.ValidationError(
                    "경매 종료 시간은 현재 시간 이후여야 합니다."
                )

        return cleaned_data
