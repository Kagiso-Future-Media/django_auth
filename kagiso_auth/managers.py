from django.contrib.auth.models import BaseUserManager


class AuthManager(BaseUserManager):

    def create_user(self, email, password=None, **other_fields):
        user = self.model(email=self.normalize_email(email), **other_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **other_fields):
        other_fields = other_fields or {}
        other_fields['is_superuser'] = True
        return self.create_user(email, password, **other_fields)
