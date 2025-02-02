from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import CustomUser


class CustomUserCreationForm(forms.ModelForm):
    """
    A custom form to create users, based on the CustomUser model.
    This form has custom validations and error handling.
    """

    password = forms.CharField(
        widget=forms.PasswordInput(),
        required=True,
        help_text="Password is required for registration",
    )

    class Meta:
        """
        Meta class to define fields of the form and the model it uses
        """

        model = CustomUser
        fields = ("email", "username", "first_name", "role")

    def clean_password(self):
        """
        A method to validate password, with custom validations if needed
        """
        password = self.cleaned_data.get("password")
        try:
            validate_password(password)
        except ValidationError as e:
            raise forms.ValidationError(e)

        return password

    def save(self, commit=True):
        """
        A method to save the form data, and set the password before saving.
        """
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
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
