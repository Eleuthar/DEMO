from django.contrib import admin
from .models import Friend, Belonging, Borrowing


admin.site.register([Friend, Belonging, Borrowing])
