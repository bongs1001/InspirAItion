from django.contrib import admin

# Register your models here.
from app.models import (
    Post,
    Comment,
    AIGeneration,
    TagUsage,
    Like,
    FrameType,
    ProductSize,
    FinishType,
    GoodsItem,
    # Order
)

admin.site.register(Post)

@admin.register(FrameType)
class FrameTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_addition', 'is_active']
    list_editable = ['price_addition', 'is_active']
    search_fields = ['name', 'description']

@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ['name', 'width', 'height', 'base_price', 'price_multiplier', 'is_active']
    list_editable = ['base_price', 'price_multiplier', 'is_active']
    search_fields = ['name']

@admin.register(FinishType)
class FinishTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_addition', 'is_active']
    list_editable = ['price_addition', 'is_active']
    search_fields = ['name', 'description']

@admin.register(GoodsItem)
class GoodsItemAdmin(admin.ModelAdmin):
    list_display = ['post', 'frame_type', 'size', 'finish_type', 'final_price', 'created_at']
    list_filter = ['frame_type', 'size', 'finish_type']
    search_fields = ['post__title']
    readonly_fields = ['final_price']

# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ['id', 'user', 'goods_item', 'quantity', 'total_price', 'status', 'created_at']
#     list_filter = ['status', 'created_at']
#     search_fields = ['user__username', 'goods_item__post__title']
#     readonly_fields = ['total_price']