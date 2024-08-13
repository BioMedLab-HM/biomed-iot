import re
from django import forms
from datetime import datetime, timedelta
# from django.utils import timezone
# from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Profile, CustomUser
from django.utils.translation import gettext_lazy as _


class UserLoginForm(AuthenticationForm):
    # The 'username' field can be either a username or an email
    # depending if UsernameAuthBackend or EmailAuthBackend is used
    username = forms.CharField(label=_('Email'), widget=forms.TextInput(attrs={'autofocus': True}))

    error_messages = {
        'invalid_login': _('Please enter a correct email and password. Note that both fields are case-sensitive.'),
        'inactive': _('This account is inactive.'),
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


class MqttClientForm(forms.Form):
    textname = forms.CharField(label='Device Name', max_length=30, required=True)


class DeleteDataForm(forms.Form):
    measurement = forms.ChoiceField(label="Select Measurement", required=True)
    tags = forms.CharField(label='Tags', max_length=1000, required=False, help_text="Format: key1=value1,key2=value2")
    start_time = forms.DateTimeField(
        label='Start Time',
        input_formats=['%Y-%m-%d %H:%M:%S'],  # User-friendly input format
        required=True,
        initial='1970-01-01 00:00:00',
        help_text='Format: yyyy-MM-dd hh:mm:ss'
    )
    end_time = forms.DateTimeField(
        label='End Time',
        input_formats=['%Y-%m-%d %H:%M:%S'],  # User-friendly input format
        required=True,
        # initial=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        # initial=lambda: datetime.now().replace(hour=23, minute=59, second=59).strftime("%Y-%m-%d %H:%M:%S"),
        initial=lambda: (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
        help_text='Format: yyyy-MM-dd hh:mm:ss'
    )

    def __init__(self, measurements_choices, *args, **kwargs):
        super(DeleteDataForm, self).__init__(*args, **kwargs)
        # Ensure measurement names are displayed as they are
        self.fields['measurement'].choices = [(m, m) for m in measurements_choices]

    def clean_tags(self):
        tags_string = self.cleaned_data['tags']
        if not tags_string:
            return {}

        # Regex to match 'key=value' where key and value cannot be empty
        tag_pattern = re.compile(r'^\s*([^=\s]+)\s*=\s*([^=\s]+)\s*$')
        tags_dict = {}
        tag_pairs = tags_string.split(',')

        for pair in tag_pairs:
            match = tag_pattern.match(pair)
            if not match:
                raise forms.ValidationError(f"Tag format error in '{pair}'. Ensure format is 'key=value' "
                                            "with no empty key or value.")
            key, value = match.groups()
            tags_dict[key] = value

        return tags_dict

    def clean_start_time(self):
        start_time = self.cleaned_data['start_time']
        return start_time.strftime('%Y-%m-%dT%H:%M:%SZ')

    def clean_end_time(self):
        end_time = self.cleaned_data['end_time']
        return end_time.strftime('%Y-%m-%dT%H:%M:%SZ')


# class MqttClientForm(forms.ModelForm):
#     class Meta:
#         model = MqttClient
#         fields = ['textname']
