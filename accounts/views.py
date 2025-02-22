from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from azure.storage.blob import BlobServiceClient
from django.conf import settings
from .forms import SignUpForm, ProfileUpdateForm
from .models import Profile
from django.contrib import messages


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if not request.POST.get("agree"):
            messages.error(request, "서비스 이용 약관에 동의해주세요.")
            return render(request, "accounts/signup.html", {"form": form})
        if form.is_valid():
            user = form.save()
            profile, created = Profile.objects.get_or_create(
                user=user, defaults={"nickname": form.cleaned_data.get("nickname")}
            )
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            return redirect("/app/")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})


@login_required
def profile_update(request):
    # 프로필이 없는 경우 생성
    if not hasattr(request.user, "profile"):
        Profile.objects.create(user=request.user)

    if request.method == "POST":
        # 기존 등록된 image 값을 저장
        old_image = request.user.profile.profile_image
        form = ProfileUpdateForm(
            request.POST, request.FILES, instance=request.user.profile
        )
        if form.is_valid():
            profile = form.save(commit=False)
            if "image_file" in request.FILES and request.FILES["image_file"]:
                file = request.FILES["image_file"]
                file_extension = file.name.split(".")[-1]
                file_name = f"profile_{request.user.username}.{file_extension}"
                try:
                    blob_service_client = BlobServiceClient.from_connection_string(
                        settings.AZURE_CONNECTION_STRING
                    )
                    container_name = settings.CONTAINER_NAME
                    blob_client = blob_service_client.get_blob_client(
                        container=container_name, blob=file_name
                    )
                    blob_client.upload_blob(file, overwrite=True)
                    profile.profile_image = blob_client.url
                except Exception as e:
                    print("==== Blob 업로드 실패 ====")
                    print("에러:", str(e))
            else:
                # 새로운 이미지 파일이 등록되지 않은 경우, 기존 profile_image를 유지
                profile.profile_image = old_image
            profile.save()
            return redirect("home")
    else:
        form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, "accounts/profile_update.html", {"form": form})
