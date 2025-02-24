# import os
# import logging
# from django.core.management.base import BaseCommand
# from azure.storage.blob import BlobServiceClient
# from django.conf import settings
# from io import BytesIO
# from PIL import Image

# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
# )


# class Command(BaseCommand):
#     help = 'Generate thumbnails for all images in the container settings.CONTAINER_NAME and upload them to the "resized" container with "thumb_" prefix.'

#     def handle(self, *args, **options):
#         blob_service_client = BlobServiceClient.from_connection_string(
#             settings.AZURE_CONNECTION_STRING
#         )
#         original_container = settings.CONTAINER_NAME
#         resized_container = "resized"

#         container_client = blob_service_client.get_container_client(original_container)
#         blobs = container_client.list_blobs()
#         count = 0

#         for blob in blobs:
#             filename = blob.name
#             # 이미지 파일 확장자 확인 (예: png, jpg, jpeg)
#             if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
#                 continue

#             try:
#                 logging.info(f"Processing {filename} ...")
#                 blob_client = blob_service_client.get_blob_client(
#                     container=original_container, blob=filename
#                 )
#                 stream = blob_client.download_blob().readall()

#                 image = Image.open(BytesIO(stream))
#                 orig_width, orig_height = image.size
#                 new_width = 500
#                 new_height = int(orig_height * (new_width / orig_width))
#                 image.thumbnail((new_width, new_height))
#                 thumb_buffer = BytesIO()
#                 image.save(thumb_buffer, format="PNG")
#                 thumb_buffer.seek(0)

#                 thumb_filename = "thumb_" + filename
#                 thumb_blob_client = blob_service_client.get_blob_client(
#                     container=resized_container, blob=thumb_filename
#                 )
#                 thumb_blob_client.upload_blob(thumb_buffer.read(), overwrite=True)
#                 logging.info(
#                     f"썸네일 이미지가 Blob Storage에 저장되었습니다: {thumb_filename}"
#                 )
#                 count += 1

#             except Exception as e:
#                 logging.error(f"{filename} 처리 중 오류 발생: {str(e)}")
#         logging.info(f"총 {count}개의 이미지에 대해 썸네일을 생성하여 업로드했습니다.")
