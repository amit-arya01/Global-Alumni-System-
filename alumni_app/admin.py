from django.contrib import admin
from .models import Alumni, Adminn
# Remove admin registration since we're using custom admin authentication
admin.site.register(Alumni)
# admin.site.register(Adminn)
