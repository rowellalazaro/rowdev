from django.contrib import admin
from .models import Post
from django.contrib import admin
from .models import PostalCode

admin.site.register(Post)

@admin.register(PostalCode)
class PostalCodeAdmin(admin.ModelAdmin):
    list_display = ("city_name", "province_name", "zip_code", "psgc_city_code")
    search_fields = ("city_name", "province_name", "psgc_city_code")
