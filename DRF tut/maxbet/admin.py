from django.contrib import admin
from .models import Sport, Market, Selection, Match


admin.site.register([Sport, Market, Selection, Match])


