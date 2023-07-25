from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    uzr = models.OneToOneField(User, on_delete=models.CASCADE, related_name='uzr_profile')
    img = models.ImageField('default.jpg', upload_to='profile_pix')

    def __str__(self):
        return f"{self.uzr.username}"
