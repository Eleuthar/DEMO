from re import search
from django.contrib.auth.models import User
from .models import Profile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class UzrSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def validate(self, data):
        xss_filter = "<(?:[^>=]|='[^']*'|=\"[^\"]*\"|=[^'\"][^\\s>]*)*>"

        for uzr_input in fields:
            if re.search('xss_filter', data[uzr_input]):
                raise ValidationError(detail="Invalid input", code=400)
        
        if (
            data['first_name'] != data['first_name'].capitalize()
            or
            data['last_name'] != data['last_name'].capitalize()
        ):
            raise ValidationError(detail="First name and last name must be capitalized", code=400)
        return data


class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = ['uzr', 'full_name', 'email', 'image']
