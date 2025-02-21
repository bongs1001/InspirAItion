from collections import namedtuple
import os
import re
import logging
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from azure.storage.blob import BlobServiceClient
from django.conf import settings
from openai import AzureOpenAI
import requests
import uuid
import json
from datetime import datetime
from django.db.models import Count
from io import BytesIO
from PIL import Image
from django.db.models import Q

from util.common.azure_computer_vision import get_image_caption_and_tags
from util.common.azure_speech import synthesize_text_to_speech
from django.views.decorators.http import require_GET

from .forms import AuctionForm, PostWithAIForm, PostEditForm
from .models import AuctionStatus, Post, AIGeneration, Comment, TagUsage, Like

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("ai_generation.log"), logging.StreamHandler()],
)

GPT_CLIENT = AzureOpenAI(
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    api_key=settings.AZURE_OPENAI_API_KEY,
    api_version=settings.AZURE_OPENAI_API_VERSION,
)

DALLE_CLIENT = AzureOpenAI(
    azure_endpoint=settings.AZURE_DALLE_ENDPOINT,
    api_key=settings.AZURE_DALLE_API_KEY,
    api_version=settings.AZURE_DALLE_API_VERSION,
)


GPT_CLIENT_o3 = AzureOpenAI(
    azure_endpoint=settings.AZURE_3OMINI_ENDPOINT,
    api_key=settings.AZURE_3OMINI_API_KEY,
    api_version=settings.AZURE_3OMINI_API_VERSION,
)


def generate_stt_with_gpt4o(user_input, user_style):
    try:
        print("GPT4-o1-mini를 사용해 프롬프트를 생성합니다...")

        response = GPT_CLIENT.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""
                        You are an AI Assistant designed to take user input (`user_input`), refine it, and transform it into a high-quality prompt suitable for an image-generating AI. Follow the guidelines below:
                        1. Analyze the user's input (`user_input`) to extract the core idea or theme they want represented in the image while preserving their intent. Add relevant details only when necessary to enhance the clarity and specificity of the image request.
                        2. Ensure the generated prompt is concise, vivid, and descriptive, making it suitable for creating visually stunning illustrations through an image-generating AI. Use nouns, adjectives, and action words effectively to create a clear and compelling image.
                        3. Avoid overinterpreting or expanding the meaning of the user's input. Stay as true as possible to the user's vision while enhancing its suitability for image generation.
                        4. Remove any inappropriate expressions, such as profanity, explicit content, or violent language, from the `user_input` while maintaining the overall intent.
                        5. Translate the generated sentence into Korean to ensure accessibility for Korean-speaking users.
                        6. Generate a refined and visually inspiring prompt that ensures the user's intent is accurately expressed and optimized for generating impressive illustrations.
                        7. Provide the output prompt in Korean to facilitate the user's understanding and engagement with the image-generating AI.
                    """,
                },
                {"role": "user", "content": user_input},
            ],
        )

        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        else:
            print("응답을 생성하지 못했습니다.")
            return None

    except Exception as e:
        print("GPT4-o1-mini 호출 중 예외 발생:", str(e))
        return None


def generate_prompt_with_gpt3o(user_input):
    try:
        print("GPT-3o-mini를 사용해 프롬프트를 생성합니다...")

        response = GPT_CLIENT_o3.chat.completions.create(
            model="team6-o3-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a master prompt engineer specializing in high-end artistic image generation, with deep expertise in both traditional and digital art forms. Your role is to create sophisticated DALL-E prompts that result in museum-quality artistic outputs.

                    ##Main Guidelines

                    1. Begin every prompt with specific technical quality markers: "Ultra high resolution masterpiece", "Professional studio quality", "Award-winning artistic composition"
                    2. Incorporate advanced artistic terminology: atmospheric perspective, tonal gradation, chiaroscuro, visual weight, negative space
                    3. Specify precise artistic techniques: impasto, sfumato, glazing, color theory, golden ratio
                    4. Include detailed environmental factors: lighting quality, atmospheric conditions, textural elements
                    5. Define exact compositional elements: rule of thirds, leading lines, focal points, depth layering
                    6. Maintain strict adherence to DALL-E's content policies while maximizing artistic potential
                    7. Always provide the prompt in English, regardless of the language used in the user's request
                    8. All prompts must include at least one specific art medium, tool, or style
                    9. All prompts aim to generate artistic works

                    ##Enhanced Prompt Structure

                    [Quality Markers] + [Artistic Style] + [Subject Definition] + [Technical Specifications] + [Compositional Details] + [Lighting/Atmosphere] + [Material/Texture] + [Color Harmony]

                    ##Technical Quality Specifications

                    - Resolution: "8K ultra-detailed", "Masterwork quality", "Museum-grade resolution"
                    - Lighting: "Professional studio lighting", "Golden hour illumination", "Dramatic chiaroscuro"
                    - Composition: "Perfect golden ratio composition", "Dynamic triangular arrangement", "Baroque diagonal flow"
                    - Texture: "Hyperrealistic surface detail", "Fine art texture", "Masterful brushwork"
                    - Color: "Professional color grading", "Sophisticated color harmony", "Expert color theory application"

                    ##Advanced Artistic Elements

                    1. Compositional Techniques
                    - Dynamic symmetry
                    - Atmospheric perspective
                    - Tonal orchestration
                    - Visual hierarchy
                    - Spatial depth management

                    2. Lighting Techniques
                    - Rembrandt lighting
                    - Split lighting
                    - Ambient occlusion
                    - Volumetric lighting
                    - Global illumination

                    3. Material Rendering
                    - Surface reflection properties
                    - Subsurface scattering
                    - Material translucency
                    - Texture mapping
                    - Environmental mapping

                    4. Color Theory Application
                    - Split-complementary harmonies
                    - Analogous color schemes
                    - Temperature gradients
                    - Value relationships
                    - Chromatic intensity control

                    ##Example Premium Prompt Format

                    "Ultra high resolution masterpiece: [artistic style] rendered in extraordinary detail. [Main subject] executed with [specific technique]. Composition employing [advanced compositional technique], enhanced by [lighting specification]. [Material quality] with [texture detail]. Professional color grading featuring [color harmony] with [atmospheric effect]."

                    ##Quality Control Guidelines

                    1. Every prompt must include at least one element from each technical category
                    2. Prioritize sophisticated artistic terminology that enhances image quality
                    3. Layer multiple techniques for complex, rich results
                    4. Balance technical precision with artistic vision
                    5. Maintain clarity while incorporating advanced elements

                    ##Precautions

                    - Do not directly mention copyrighted characters or brands.
                    - Avoid violent or inappropriate content.
                    - Avoid overly complex or ambiguous descriptions, maintain clarity.
                    - Avoid words related to violence, adult content, gore, politics, or drugs.
                    - Do not use names of real people.
                    - Avoid directly mentioning specific body parts.

                    Follow these guidelines to create prompts that generate exceptional, gallery-quality artistic images while adhering to DALL-E's content policies.""",
                },
                {"role": "user", "content": user_input},
            ],
        )

        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        else:
            print("응답을 생성하지 못했습니다.")
            return None

    except Exception as e:
        print("GPT-3o-mini 호출 중 예외 발생:", str(e))
        return None


def generate_prompt_with_gpt4o(user_input):
    """GPT-4o를 사용해 DALL-E 3 프롬프트 생성"""
    try:
        logging.info("GPT-4o를 사용해 프롬프트를 생성합니다...")

        response = GPT_CLIENT.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert in converting user's natural language descriptions into DALL-E image generation prompts.
                    Please generate prompts according to the following guidelines:

                    ## Main Guidelines
                    1. Carefully analyse the user's description to identify key elements.
                    2. Use clear and specific language to write the prompt.
                    3. Include details such as the main subject, style, composition, colour, and lighting.
                    4. Appropriately utilise artistic references or cultural elements.
                    5. Add instructions about image quality or resolution if necessary.
                    6. Evaluate content policy violations and notify if blocked.
                    7. Always provide the prompt in English.

                    ## Prompt Structure
                    - Specify the main subject first, then add details.
                    - Use adjectives and adverbs for mood and style.
                    - Specify composition or perspective if needed.

                    ## Precautions
                    - No copyrighted characters or brands
                    - No violent or inappropriate content
                    - Avoid complex or ambiguous descriptions
                    - No words related to violence, adult content, gore, politics, or drugs
                    - No names or real people
                    - No specific body parts

                    ## Format Example:
                    "[Style/mood] image of [main subject]. [Detailed description]. [Composition]. [Colour/lighting]."
                    """,
                },
                {"role": "user", "content": user_input},
            ],
            temperature=0.7,
        )

        if response.choices and len(response.choices) > 0:
            generated_prompt = response.choices[0].message.content.strip()
            logging.info(f"생성된 프롬프트: {generated_prompt}")
            return generated_prompt
        return None

    except Exception as e:
        logging.error(f"GPT-4o 호출 중 예외 발생: {str(e)}", exc_info=True)
        return None


def save_image_to_blob(image_url, prompt, user_id):
    """이미지를 Azure Blob Storage에 저장하고, width 500으로 리사이즈한 썸네일을 'resized' 컨테이너에 저장"""
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        sanitised_prompt = re.sub(r'[<>:"/\\|?*]', "", prompt[:20]).strip()
        filename = f"user_{user_id}_{timestamp}_{unique_id}_{sanitised_prompt}.png"

        blob_service_client = BlobServiceClient.from_connection_string(
            settings.AZURE_CONNECTION_STRING
        )

        # 원본 이미지 업로드 (기존 container 사용)
        blob_client = blob_service_client.get_blob_client(
            container=settings.CONTAINER_NAME, blob=filename
        )
        blob_client.upload_blob(response.content, overwrite=True)
        logging.info(f"원본 이미지가 Blob Storage에 저장되었습니다: {filename}")

        # Pillow를 이용해 이미지 리사이즈 및 썸네일 생성 (width=300)
        image = Image.open(BytesIO(response.content))
        orig_width, orig_height = image.size
        new_width = 500
        new_height = int(orig_height * (new_width / orig_width))
        image.thumbnail((new_width, new_height))
        thumb_buffer = BytesIO()
        image.save(thumb_buffer, format="PNG")
        thumb_buffer.seek(0)

        # "resized" 컨테이너에 썸네일 업로드, filename 앞에 "thumb_" 접두어 추가
        thumb_filename = "thumb_" + filename
        thumb_blob_client = blob_service_client.get_blob_client(
            container="resized", blob=thumb_filename
        )
        thumb_blob_client.upload_blob(thumb_buffer.read(), overwrite=True)
        logging.info(f"썸네일 이미지가 Blob Storage에 저장되었습니다: {thumb_filename}")

        # 원본 이미지 URL 반환 (원하는 경우 썸네일 URL도 함께 반환 가능)
        return blob_client.url

    except Exception as e:
        logging.error(f"Blob Storage 저장 중 오류 발생: {str(e)}", exc_info=True)
        return None


def generate_image_with_dalle(prompt):
    """DALL-E를 사용해 이미지를 생성"""
    try:
        logging.info("DALL-E를 사용해 이미지를 생성합니다...")

        result = DALLE_CLIENT.images.generate(model="dall-e-3", prompt=prompt, n=1)

        if result and result.data:
            image_url = result.data[0].url
            logging.info(f"DALL-E 호출 성공! 생성된 이미지 URL: {image_url}")
            return image_url
        return None

    except Exception as e:
        logging.error(f"DALL-E 호출 중 예외 발생: {str(e)}", exc_info=True)
        return None


@login_required
def generate_image(request):
    """이미지 생성 뷰"""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    prompt = request.POST.get("prompt", "").strip()
    if not prompt:
        return JsonResponse({"error": "프롬프트를 입력해주세요."}, status=400)

    try:
        # generated_prompt = generate_prompt_with_gpt4o(prompt)
        generated_prompt = generate_prompt_with_gpt3o(prompt)
        if not generated_prompt:
            return JsonResponse({"error": "프롬프트 생성에 실패했습니다."}, status=500)

        image_url = generate_image_with_dalle(generated_prompt)
        if not image_url:
            return JsonResponse({"error": "이미지 생성에 실패했습니다."}, status=500)

        blob_url = save_image_to_blob(image_url, generated_prompt, request.user.id)
        if not blob_url:
            return JsonResponse({"error": "이미지 저장에 실패했습니다."}, status=500)

        return JsonResponse(
            {"image_url": blob_url, "generated_prompt": generated_prompt}
        )

    except Exception as e:
        logging.error(f"이미지 생성 중 오류 발생: {str(e)}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["POST"])
def read_text(request: HttpRequest) -> HttpResponse:
    try:
        data = json.loads(request.body)
        caption = data.get("caption", "").strip()
        if not caption:
            return JsonResponse({"error": "캡션이 제공되지 않았습니다."}, status=400)
        audio_data = synthesize_text_to_speech(caption)
        if not audio_data:
            raise Exception("음성 데이터를 생성하지 못했습니다.")
        response = HttpResponse(audio_data, content_type="audio/wav")
        response["Content-Disposition"] = 'attachment; filename="caption.wav"'
        return response
    except Exception as e:
        logging.error("read_text 에러", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def index(request: HttpRequest) -> HttpResponse:
    ai_images = None
    if request.user.is_authenticated:
        ai_images = AIGeneration.objects.filter(user=request.user).order_by(
            "-created_at"
        )[:1]
    ai_images = None
    if request.user.is_authenticated:
        ai_images = AIGeneration.objects.filter(user=request.user).order_by(
            "-created_at"
        )[:1]
    return render(request, "app/home.html", {"ai_images": ai_images})


@login_required
def post_detail(request: HttpRequest, pk: int) -> HttpResponse:
    post = get_object_or_404(Post.objects.select_related("user__profile"), pk=pk)
    user_liked = (
        Like.objects.filter(user=request.user, post=post).exists()
        if request.user.is_authenticated
        else False
    )
    curation_text = ""
    previous_url = request.META.get("HTTP_REFERER", "")
    logging.info(f"이전 화면의 주소: {previous_url}")
    return render(
        request,
        "app/post_detail.html",
        {
            "post": post,
            "curation_text": curation_text,
            "previous_url": previous_url,
            "user_liked": user_liked,
        },
    )


@login_required
@require_http_methods(["POST"])
def generate_curation(request, pk):
    post = get_object_or_404(Post.objects.select_related("user__profile"), pk=pk)
    caption = post.caption
    tags = post.tags

    caption_str = caption[0] if caption else ""
    try:
        data = json.loads(request.body)
        selected_style = data.get("style", "Emotional")
    except Exception:
        selected_style = "Emotional"

    # generate_ai_curation returns a dict with various style keys.
    curation_text = generate_ai_curation(
        selected_style, post.title, caption_str, ", ".join(tags)
    )
    return JsonResponse({"curation_text": curation_text})


def generate_ai_curation(selected_style, user_prompt, captions, tags):
    """
    한글로 각 스타일별 큐레이션을 생성하는 함수

    Args:
        user_prompt (str): 사용자 프롬프트
        captions (str): 이미지 설명
        tags (str): 태그들

    Returns:
        dict: 한글 스타일명과 큐레이션을 담은 딕셔너리
    """

    combined_text = f"프롬프트: {user_prompt}\n이미지 설명: {captions}\n태그: {tags}"

    # 스타일별 프롬프트 설정
    style_prompts = {
        "Emotional": """Explore the emotions and sentiments contained in this artwork in depth. Write lyrically, including the following elements:
            - The main emotions and atmosphere conveyed by the work
            - Emotional responses evoked by visual elements
            - The special emotions given by the moment in the work
            - Empathy and resonance that viewers can feel
            - Lyrical characteristics and poetic expressions of the work""",
        "Interpretive": """Analyze the meaning and artistic techniques of the work in depth. Interpret it by including the following elements:
            - The main visual elements of the work and their symbolism
            - The effects of composition and color sense
            - The artist's intention and message
            - Artistic techniques used and their effects
            - Philosophical/conceptual meaning conveyed by the work""",
        "Historical": """Analyze the work in depth in its historical and art historical context. Explain it by including the following elements:
            - The historical background and characteristics of the era in which the work was produced
            - Relationship with similar art trends or works
            - Position and significance in modern art history
            - Artistic/social impact of the work
            - Interpretation of the work in its historical context""",
        "Critical": """Provide a professional and balanced critique of the work. Evaluate it by including the following elements:
            - Technical completeness and artistry of the work
            - Analysis of creativity and innovation
            - Strengths and areas for improvement
            - Artistic achievement and limitations
            - Uniqueness and differentiation of the work""",
        "Narrative": """Unravel the work into an attractive story. Describe it by including the following elements:
            - Vivid description of the scene in the work
            - Relationship and story between the elements of appearance
            - Flow and changes in time in the work
            - Hidden drama and narrative in the scene
            - Context before and after that viewers can imagine""",
        "Trend": """Analyze the work from the perspective of contemporary art trends. Evaluate it by including the following elements:
            - Relevance to contemporary art trends
            - Digital/technological innovation elements
            - Meaning in the context of modern society/culture
            - Contact with the latest art trends
            - Implications for future art development""",
        "Money": """You are an art price evaluation expert with decades of experience in the art market. Provide a detailed and professional price analysis for the given artwork. Consider the following elements to determine and explain the precise price of the work:
            - Artist's reputation and market value
            - Size, materials, and year of creation of the artwork
            - Rarity and condition of the piece
            - Recent auction prices of similar works
            - Current art market trends and demand
            The price evaluation should be written in a specific and persuasive manner, clearly revealing the monetary value of the work from a professional perspective. Finally, present an estimated price range and explain its basis in detail. Ensure that your analysis does not exceed 800 characters.""",
        "Praise": """You are a passionate art advocate with a deep affection and understanding of contemporary art. Provide a positive and inspiring analysis of the given artwork. Consider the following elements to enthusiastically praise the work:
            - Innovative aspects and originality of the piece
            - Excellent use of color and composition
            - The artist's vision and its superb expression
            - Emotional and intellectual impact on the viewer
            - Significance in the context of contemporary art history
            The analysis should be written in an enthusiastic and persuasive tone.Emphasize the work's strengths and vividly describe its artistic value. Explain how the piece stimulates the audience's emotions and presents new perspectives. Also, mention the positive influence this work has on the art world and the inspiration it can provide to future generations. 
            Throughout your curation, intersperse appropriate exclamations and expressions of awe to convey your genuine excitement and admiration for the artwork. Use phrases like "Wow!", "Incredible!", "Absolutely stunning!", or "What a masterpiece!" to enhance the enthusiastic tone of your analysis. Ensure that your analysis does not exceed 800 characters.""",
        "Blind": """You are an expert in describing images for visually impaired individuals. Your goal is to provide clear, detailed, and vivid descriptions that help them mentally visualize the image.
            #Key Elements to Include
            - General composition and main elements of the image.
            - Detailed descriptions of colors, shapes, and textures.
            - Spatial relationships and arrangement of objects.
            - Mood or emotions conveyed by the image.
            - Important details or unique characteristics.
            #Guidelines for Writing
            - Use concise yet rich descriptions.
            - Relate visual elements to tactile or auditory experiences.
            - Specify positions using clear references (e.g., "at the top center").
            - Describe colors using relatable comparisons (e.g., "sky blue like a clear summer day").
            - Focus on concrete, objective details rather than abstract concepts.
            - Provide context or purpose of the image to aid understanding.
            #Objective
            Enable visually impaired individuals to form a vivid mental picture of the image through your descriptive language.""",
    }

    # 결과를 저장할 딕셔너리
    curations = {}

    # 선택된 스타일에 해당하는 큐레이션 생성
    style_prompt = style_prompts.get(selected_style, "")
    if style_prompt:
        try:
            response = GPT_CLIENT.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are an art curation expert. Provide a very detailed and professional analysis of the given work.
                        {style_prompt} The analysis should be written in a specific and persuasive manner,
                        and should clearly reveal the characteristics and value of the work from a professional perspective.
                        As an expert in evaluating artwork, please provide an assessment of the piece within 100 words, utilizing the provided information.
                        Please write a curation in Korean based on the following information.""",
                    },
                    {"role": "user", "content": combined_text},
                ],
            )
            curations[selected_style] = response.choices[0].message.content
        except Exception as e:
            curations[selected_style] = (
                f"Error generating {selected_style} curation: {str(e)}"
            )
    else:
        curations[selected_style] = "Invalid style selected."

    return curations[selected_style]


@login_required
def create_post(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = PostWithAIForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user

            generated_image_url = request.POST.get("generated_image_url")
            generated_prompt = request.POST.get("generated_prompt")
            caption, tags = get_image_caption_and_tags(generated_image_url)

            if generated_image_url:
                blob_url = save_image_to_blob(
                    generated_image_url, form.cleaned_data["prompt"], request.user.id
                )
                if blob_url:
                    post.image = generated_image_url

                    AIGeneration.objects.create(
                        user=request.user,
                        prompt=form.cleaned_data["prompt"],
                        generated_prompt=generated_prompt,
                        image_url=blob_url,
                    )
            if generated_prompt:
                post.generated_prompt = generated_prompt
            if caption:
                post.caption = caption[0]
            if tags:
                # tags를 리스트 형태로 저장
                post.tags = tags

            post.save()
            form.save_m2m()

            # 분석된 tags 정보를 TagUsage 업데이트
            if tags:
                update_tag_usage_on_create(tags)

            return redirect("post_detail", pk=post.pk)
    else:
        form = PostWithAIForm()
    return render(request, "app/create_post.html", {"form": form})


def update_tag_usage_on_create(tags):
    if not isinstance(tags, list):
        return
    for tag in tags:
        tag_usage, created = TagUsage.objects.get_or_create(tag=tag)
        tag_usage.count += 1
        tag_usage.save()


def update_tag_usage_on_delete(tags):
    if not isinstance(tags, list):
        return
    for tag in tags:
        try:
            tag_usage = TagUsage.objects.get(tag=tag)
            if tag_usage.count > 0:
                tag_usage.count -= 1
                tag_usage.save()
        except TagUsage.DoesNotExist:
            continue


@login_required
def edit_post(request: HttpRequest, pk: int) -> HttpResponse:
    """게시물 수정 (이미지 수정 불가)"""
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = PostEditForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            # 수정: is_public 필드 업데이트 추가
            post.is_public = True if request.POST.get("is_public") else False
            post.save()
            return redirect("post_detail", pk=pk)
    else:
        form = PostEditForm(instance=post)
    return render(request, "app/edit_post.html", {"form": form, "post": post})


@login_required
def delete_post(request: HttpRequest, pk: int) -> HttpResponse:
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        previous_url = request.META.get("HTTP_REFERER", "home")
        logging.info(f"이전 화면의 주소: {previous_url}")
        if post.tags:
            update_tag_usage_on_delete(post.tags)
        post.delete()

        if post.is_public:
            return redirect("public_gallery")
        else:
            return redirect("my_gallery")
    return render(request, "app/post_detail.html", {"post": post})


from django.template.loader import render_to_string


def my_gallery(request):
    search_query = request.GET.get("search", "")
    tag_filter = request.GET.get("tag", "")
    sort_by = request.GET.get("sort", "date")
    ownership_filter = request.GET.get("ownership", "all")

    user_posts = Post.objects.filter(current_owner=request.user)

    user_tag_counts = {}
    for post in user_posts:
        if post.tags:
            for tag in post.tags:
                user_tag_counts[tag] = user_tag_counts.get(tag, 0) + 1

    UserTag = namedtuple("UserTag", ["tag", "count"])
    top_tags = [
        UserTag(tag=tag, count=count)
        for tag, count in sorted(
            user_tag_counts.items(), key=lambda x: x[1], reverse=True
        )
    ][:10]

    posts_qs = Post.objects.filter(current_owner=request.user).annotate(
        like_count=Count("likes")
    )

    if ownership_filter == 'created':
        posts_qs = Post.objects.filter(original_creator=request.user)
    elif ownership_filter == 'all':
        posts_qs = Post.objects.filter(
            Q(current_owner=request.user) | Q(original_creator=request.user)
        )

    if search_query:
        posts_qs = posts_qs.filter(title__icontains=search_query)

    if sort_by == "likes":
        posts_qs = posts_qs.order_by("-like_count", "-date_posted")
    else:
        posts_qs = posts_qs.order_by("-date_posted")

    if tag_filter:
        if tag_filter in user_tag_counts:
            posts_list = [
                post for post in posts_qs if post.tags and tag_filter in post.tags
            ]
        else:
            posts_list = []
    else:
        posts_list = list(posts_qs)

    page = int(request.GET.get("page", "1"))
    post_cnt = 9
    offset = (page - 1) * post_cnt
    total_count = len(posts_list)
    posts = posts_list[offset : offset + post_cnt]
    has_more = (offset + post_cnt) < total_count

    for post in posts:
        if post.image:
            post.thumb = post.image.replace("uploads/", "resized/thumb_")

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html_fragment = render_to_string(
            "app/_post_list.html", {"posts": posts}, request=request
        )
        return JsonResponse({"html": html_fragment, "has_more": has_more})

    return render(
        request,
        "app/gallery.html",
        {
            "posts": posts,
            "gallery_type": "personal",
            "search_query": search_query,
            "top_tags": top_tags,
            "selected_tag": tag_filter,
            "has_more": has_more,
            "sort_by": sort_by,
        },
    )


def public_gallery(request):
    search_query = request.GET.get("search", "")
    tag_filter = request.GET.get("tag", "")
    sort_by = request.GET.get("sort", "likes")
    page = int(request.GET.get("page", "1"))
    post_cnt = 9
    offset = (page - 1) * post_cnt

    posts_qs = Post.objects.filter(is_public=True).annotate(like_count=Count("likes"))
    if search_query:
        posts_qs = posts_qs.filter(title__icontains=search_query)

    total_count = posts_qs.count()

    if sort_by == "likes":
        posts_qs = posts_qs.order_by("-like_count", "-date_posted")
    else:
        posts_qs = posts_qs.order_by("-date_posted")

    if tag_filter:
        all_posts = list(posts_qs)
        posts_list = [
            post for post in all_posts if post.tags and tag_filter in post.tags
        ]
        posts = posts_list[offset : offset + post_cnt]
        total_count = len(posts_list)
    else:
        posts = posts_qs[offset : offset + post_cnt]

    has_more = (offset + post_cnt) < total_count

    # 추가: 각 포스트의 image 필드에 uploads/를 resized/thumb_로 대체하여 썸네일 URL을 post.thumb에 저장
    for post in posts:
        if post.image:
            post.thumb = post.image.replace("uploads/", "resized/thumb_")

    # AJAX 요청 시 HTML 프래그먼트 반환
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html_fragment = render_to_string(
            "app/_post_list.html", {"posts": posts}, request=request
        )
        return JsonResponse({"html": html_fragment, "has_more": has_more})

    top_tags = TagUsage.objects.order_by("-count")[:10]
    top_posts = get_top_liked_posts()
    for post in top_posts:
        if post.image:
            post.thumb = post.image.replace("uploads/", "resized/thumb_")

    return render(
        request,
        "app/gallery.html",
        {
            "posts": posts,
            "gallery_type": "public",
            "search_query": search_query,
            "top_tags": top_tags,
            "selected_tag": tag_filter,
            "has_more": has_more,
            "sort_by": sort_by,
            "top_posts": top_posts,
        },
    )


@require_http_methods(["GET", "POST"])
def comment_list_create(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == "GET":
        comments = Comment.objects.filter(post=post).select_related(
            "author", "author__profile"
        )
        data = [
            {
                "id": comment.id,
                "message": comment.message,
                "author": comment.author_nickname if comment.author else "Anonymous",
                "created_at": comment.created_at.isoformat(),
            }
            for comment in comments
        ]
        return JsonResponse({"comments": data})

    elif request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

        try:
            data = json.loads(request.body)
            message = data.get("message", "").strip()

            if not message:
                return JsonResponse({"error": "댓글 내용을 입력해주세요."}, status=400)

            comment = Comment.objects.create(
                post=post, author=request.user, message=message
            )

            return JsonResponse(
                {
                    "id": comment.id,
                    "message": comment.message,
                    "author": comment.author.username,
                    "created_at": comment.created_at.isoformat(),
                },
                status=201,
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "잘못된 요청입니다."}, status=400)


@require_http_methods(["DELETE", "PATCH"])
def comment_detail(request, pk):
    comment = get_object_or_404(Comment, id=pk)

    if not request.user.is_authenticated:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    if comment.author != request.user:
        return JsonResponse({"error": "권한이 없습니다."}, status=403)

    if request.method == "DELETE":
        comment.delete()
        return JsonResponse({"message": "댓글이 삭제되었습니다."})

    elif request.method == "PATCH":
        try:
            data = json.loads(request.body)
            message = data.get("message", "").strip()

            if not message:
                return JsonResponse({"error": "댓글 내용을 입력해주세요."}, status=400)

            comment.message = message
            comment.save()

            return JsonResponse(
                {
                    "id": comment.id,
                    "message": comment.message,
                    "author": comment.author.username,
                    "created_at": comment.created_at.isoformat(),
                    "updated_at": comment.updated_at.isoformat(),
                }
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "잘못된 요청입니다."}, status=400)


@login_required
def custom_admin(request):
    return redirect("admin")  # 관리자 페이지로 리디렉션


def home(request):
    return render(request, "app/home.html")


def about(request):
    return render(request, "app/about.html")


def services(request):
    return render(
        request, "app/services.html"
    )  # html정리 전(main 에는 about으로 연결해둠)


def our_team(request):
    return render(
        request, "app/our_team.html"
    )  # html정리 전(main 에는 about으로 연결해둠


def board(request):
    return render(request, "app/board.html")  # 새 게시판 앱 생성 예정


def contact_us(request):
    return render(request, "app/contact_us.html")  # email_app 연결 예정정


def ai_play(request):
    return render(request, "app/ai_play.html")  # html만 있고, 아직 기능 merge 전


def index_ai(request):
    return render(request, "app/index_ai.html")


def send_email(request):
    return render(request, "email_app/send_email.html")


def email_list(request):
    return render(request, "email_app/email_list.html")


def email_detail(request, email_id):
    return render(request, "email_app/email_detail.html")


def fullscreen_gallery(request):
    """전체 화면 갤러리 뷰"""
    posts = (
        Post.objects.filter(is_public=True)
        .exclude(image__isnull=True)
        .exclude(image__exact="")
        .order_by("-date_posted")
    )

    return render(request, "app/fullscreen_gallery.html", {"posts": posts})


@login_required
def like_post(request, pk):
    try:
        post = get_object_or_404(Post, pk=pk)
        like, created = Like.objects.get_or_create(user=request.user, post=post)

        if not created:
            like.delete()
            liked = False

        else:
            liked = True

        return JsonResponse(
            {
                "liked": liked,
                "likes_count": post.likes_count,
                "is_popular": post.is_popular,
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_tag_image_urls(tags):
    """각 태그별 가장 좋아요가 많은 이미지 URL을 가져온다."""
    tag_images = {}
    for tag_obj in tags:
        tag = tag_obj.tag
        most_liked_post = (
            Post.objects.filter(tags__contains=[tag]).order_by("-likes_count").first()
        )
        tag_images[tag] = most_liked_post.image if most_liked_post else None
    return tag_images


def get_top_liked_posts():
    return (
        Post.objects.filter(is_public=True)
        .annotate(like_count=Count("likes"))
        .order_by("-like_count")[:3]
    )


@require_http_methods(["POST"])
def gpt4o_stt_api(request):
    """
    POST 데이터로 전달받은 'text'와 'style'을 인자로 하여
    generate_stt_with_gpt3o(user_input, user_style)를 호출한 후 결과를 반환.
    """
    try:
        user_input = request.POST.get("text", "").strip()
        user_style = request.POST.get("style", "default").strip()
        if not user_input:
            return JsonResponse({"error": "텍스트가 제공되지 않았습니다."}, status=400)
        result = generate_stt_with_gpt4o(user_input, user_style)
        if result is None:
            return JsonResponse({"error": "AI 처리 실패"}, status=500)
        return JsonResponse({"result": result})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def register_auction(request, post_id):
    post = get_object_or_404(Post, id=post_id, current_owner=request.user)

    if request.method == "POST":
        form = AuctionForm(request.POST)
        if form.is_valid():
            auction = form.save(commit=False)
            auction.post = post
            auction.seller = request.user
            auction.current_price = form.cleaned_data['start_price']
            auction.status = AuctionStatus.ACTIVE
            auction.save()
            return redirect('auction_detail', auction_id=auction.id)
    else:
        form = AuctionForm()

    return render(request, 'app/auction/register.html', {
        'form': form,
        'post': post
    })