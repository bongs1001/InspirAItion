from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile


class SignUpForm(UserCreationForm):
    nickname = forms.CharField(
        max_length=50,
        required=True,
        help_text="사용하실 닉네임을 입력해주세요.",
        widget=forms.TextInput(attrs={"placeholder": "닉네임"}),
    )

    class Meta:
        model = User
        fields = ("username", "nickname", "password1", "password2")


class ProfileUpdateForm(forms.ModelForm):
    profile_image = forms.URLField(required=False, widget=forms.HiddenInput())
    image_file = forms.FileField(
        required=False, widget=forms.FileInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = Profile
        fields = ["nickname", "profile_image", "user_style"]

    def clean_profile_image(self):
        image = self.cleaned_data.get("image_file")
        if image:
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("이미지 크기가 5MB를 초과할 수 없습니다.")
            if not image.content_type.startswith("image"):
                raise forms.ValidationError("이미지 파일만 업로드할 수 있습니다.")

        return image
