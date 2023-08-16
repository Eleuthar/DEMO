from django.contrib import admin
from .models import Post

class PostAdmin(admin.ModelAdmin):
    readonly_fields = ['pk']
    list_display = ('pk', '__str__',)

admin.site.register(Post, PostAdmin)
