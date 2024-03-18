from django import forms
# from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Profile, CustomUser, MqttClient
from django.utils.translation import gettext_lazy as _


class UserLoginForm(AuthenticationForm):  # Use the default authentication form as a base
    # username = forms.CharField(label="Email")  # disallow login with username for username may be shared with other users for special purposes
    # username = forms.EmailField(label=_("Email"), widget=forms.TextInput(attrs={'autofocus': True}))
    username = forms.CharField(label=_("Email"), widget=forms.TextInput(attrs={'autofocus': True}))

    error_messages = {
        'invalid_login': _(
            "Please enter a correct email and password. Note that both fields may be case-sensitive."
        ),
        'inactive': _("This account is inactive."),
    }

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']  # form fields in respective order


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = CustomUser
        fields = ['username', 'email']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image']


class MqttClientForm(forms.ModelForm):
    class Meta:
        model = MqttClient
        fields = ['textname']
