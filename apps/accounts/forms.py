from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import CustomerProfile, CustomUser, DriverProfile, ShopProfile


class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(),
        required=True,
        help_text="Password is required for registration",
    )

    class Meta:
        model = CustomUser
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "company_name",
            "role",
        ]

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance", None)
        super().__init__(*args, **kwargs)

        if instance:
            self.fields.pop("password")

            for field in self.fields.values():
                field.label = None

            self.fields["role"].choices = [
                choice for choice in self.fields["role"].choices if choice[0] != "admin"
            ]
        else:
            self.fields["role"].initial = "shop"

    def clean_password(self):
        password = self.cleaned_data.get("password")
        try:
            validate_password(password)
        except ValidationError as e:
            raise forms.ValidationError(e)

        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
            }
        )
    )


class DriverProfileForm(forms.ModelForm):
    class Meta:
        model = DriverProfile
        fields = ["vehicle_type", "capacity"]

    def clean_capacity(self):
        capacity = self.cleaned_data.get("capacity")
        if capacity <= 0:
            raise forms.ValidationError("Capacity must be a positive number.")
        return capacity


class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = CustomerProfile
        fields = ["payment_methods", "address"]


class ShopProfileForm(forms.ModelForm):
    class Meta:
        model = ShopProfile
        fields = ["product_categories", "accepted_payment_methods", "address"]
