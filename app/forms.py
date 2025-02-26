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
        widget=forms.DateTimeInput(attrs={
            "type": "datetime-local", 
            "class": "form-control",
            "step": "60"  # 초 단위 입력 방지 (1분 단위로만 선택 가능)
        }),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M'],
    )
    end_time = forms.DateTimeField(
        label="경매 종료 시간",
        widget=forms.DateTimeInput(attrs={
            "type": "datetime-local", 
            "class": "form-control",
            "step": "60"  # 초 단위 입력 방지 (1분 단위로만 선택 가능)
        }),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M'],
    )
    # 소수점 없는 정수 필드로 변경
    start_price = forms.IntegerField(
        label="시작가",
        min_value=1000,
        widget=forms.NumberInput(attrs={
            "placeholder": "시작가를 입력하세요 (최소 1,000원)",
            "class": "form-control"
        }),
    )

    class Meta:
        model = Auction
        fields = ["start_price", "start_time", "end_time"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 기본값 설정
        if not self.is_bound:  # 폼이 아직 데이터로 바인딩되지 않은 경우에만
            now = timezone.now()
            start_time = now + timedelta(minutes=5)
            end_time = start_time + timedelta(minutes=10)
            self.initial['start_time'] = start_time.strftime('%Y-%m-%dT%H:%M')
            self.initial['end_time'] = end_time.strftime('%Y-%m-%dT%H:%M')
            self.initial['start_price'] = 1000  # 기본 시작가

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        # 필드가 존재하는 경우에만 유효성 검사 수행
        if start_time and end_time:
            now = timezone.now()
            
            # 시작 시간이 현재 시간 이후인지 확인
            if start_time < now:
                self.add_error('start_time', "경매 시작 시간은 현재 시간 이후여야 합니다.")
            
            # 종료 시간이 시작 시간 이후인지 확인
            if end_time <= start_time:
                self.add_error('end_time', "경매 종료 시간은 시작 시간 이후여야 합니다.")
            
            # 종료 시간이 현재 시간 이후인지 확인
            if end_time < now:
                self.add_error('end_time', "경매 종료 시간은 현재 시간 이후여야 합니다.")

        return cleaned_data