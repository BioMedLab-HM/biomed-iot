import re
from django import forms
from datetime import datetime, timedelta
from django.utils import timezone
from datetime import timezone as dt_tz
# from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Profile, CustomUser
from .services.influx_data_utils import InfluxDataManager
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
    same_topic = forms.BooleanField(label='in-out', required=False)

class SelectDataForm(forms.Form):
    measurement = forms.ChoiceField(label="Select Measurement", required=True)
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
    tags = forms.MultipleChoiceField(
        label = "Tags (Use tags to select only certain tagged data points. Leave empty to select the entire measurement.)",
        required=False,
        widget=forms.SelectMultiple,
        help_text="Select one or more (key=value).",
    )

    def __init__(self, measurements_choices, *args, **kwargs):
        user = kwargs.pop("user")            # pass request.user into the form
        super().__init__(*args, **kwargs)

        # measurement placeholder + real choices
        placeholder = [("", "-- Select Measurement --")]
        self.fields["measurement"].choices = placeholder + [(m, m) for m in measurements_choices]
        self.fields["measurement"].initial = ""

        # tags start empty; if form is bound with a measurement, pre-populate
        self.fields["tags"].choices = []
        meas = self.data.get("measurement") or self.initial.get("measurement")
        if meas:
            mgr = InfluxDataManager(user)
            pairs = mgr.list_tag_pairs(meas)
            self.fields["tags"].choices = [(p, p) for p in pairs]

    def clean_measurement(self):
        val = self.cleaned_data["measurement"]
        if not val:
            raise forms.ValidationError("You must select a measurement.")
        return val

    def clean_tags(self):
        """
        Convert ['key=val',...] into {'key':'val',...}.
        """
        raw = self.cleaned_data["tags"]
        out: dict[str,str] = {}
        for pair in raw:
            if "=" not in pair:
                raise forms.ValidationError(f"Bad tag: {pair!r}")
            k, v = pair.split("=", 1)
            out[k] = v
        return out

    def clean_start_time(self):
        # start_time = self.cleaned_data['start_time']
        # return start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        return self._utc_rfc3339(self.cleaned_data["start_time"])

    def clean_end_time(self):
        # end_time = self.cleaned_data['end_time']
        # return end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        return self._utc_rfc3339(self.cleaned_data["end_time"])

    def _utc_rfc3339(self, dt):
        """
        Ensure *dt* is aware, convert to UTC, and render as RFC-3339.
        Works on both summer (+02:00) and winter (+01:00).
        """
        if timezone.is_naive(dt):              # should not happen with USE_TZ=True,
            dt = timezone.make_aware(dt)       # but keeps the code future-proof

        return dt.astimezone(dt_tz.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

# OLD VERSION, KEEP FOR REFERENCE
# class SelectDataForm(forms.Form):
#     measurement = forms.ChoiceField(
#         label="Select Measurement",
#         required=True
#         )
#     tags = forms.CharField(
#         label='Tags (Optional Advanced Feature!)',
#         max_length=1000,
#         required=False,
#         help_text="Example: fieldname=temperature,fieldname=humidity -> selects values (not columns) for the fields 'temperature' and 'humidity' from the selected measurement."
#         )
#     start_time = forms.DateTimeField(
#         label='Start Time',
#         input_formats=['%Y-%m-%d %H:%M:%S'],  # User-friendly input format
#         required=True,
#         initial='1970-01-01 00:00:00',
#         help_text='Format: yyyy-MM-dd hh:mm:ss'
#         )
#     end_time = forms.DateTimeField(
#         label='End Time',
#         input_formats=['%Y-%m-%d %H:%M:%S'],  # User-friendly input format
#         required=True,
#         # initial=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         # initial=lambda: datetime.now().replace(hour=23, minute=59, second=59).strftime("%Y-%m-%d %H:%M:%S"),
#         initial=lambda: (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
#         help_text='Format: yyyy-MM-dd hh:mm:ss'
#         )

#     def __init__(self, measurements_choices, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         # 1) define your placeholder label
#         placeholder = "-- Select Measurement --"

#         # 2) build choices with a blank first entry
#         blank_choice = [("", placeholder)]
#         actual_choices = [(m, m) for m in measurements_choices]
#         self.fields['measurement'].choices = blank_choice + actual_choices

#         # 3) ensure the blank is selected by default
#         self.fields['measurement'].initial = ""

#     def clean_measurement(self):
#         data = self.cleaned_data['measurement']
#         if not data:
#             raise forms.ValidationError("You must select a measurement.")
#         return data

#     def clean_tags(self):
#         tags_string = self.cleaned_data['tags']
#         if not tags_string:
#             return {}

#         # Regex to match 'key=value' where key and value cannot be empty
#         tag_pattern = re.compile(r'^\s*([^=\s]+)\s*=\s*([^=\s]+)\s*$')
#         tags_dict = {}
#         tag_pairs = tags_string.split(',')

#         for pair in tag_pairs:
#             match = tag_pattern.match(pair)
#             if not match:
#                 raise forms.ValidationError(f"Tag format error in '{pair}'. Ensure format is 'key=value' "
#                                             "with no empty key or value.")
#             key, value = match.groups()
#             tags_dict[key] = value

#         return tags_dict

#     def clean_start_time(self):
#         start_time = self.cleaned_data['start_time']
#         return start_time.strftime('%Y-%m-%dT%H:%M:%SZ')

#     def clean_end_time(self):
#         end_time = self.cleaned_data['end_time']
#         return end_time.strftime('%Y-%m-%dT%H:%M:%SZ')


# class MqttClientForm(forms.ModelForm):
#     class Meta:
#         model = MqttClient
#         fields = ['textname']
