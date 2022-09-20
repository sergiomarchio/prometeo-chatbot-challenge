from django import forms
from django.utils.translation import gettext_lazy as _


class LoginForm(forms.Form):
    attrs = {
        'id': "input-field",
        'class': "input-field",
        'placeholder': 'API key'
    }

    api_key = forms.CharField(label="",
                              widget=forms.TextInput(attrs=attrs))


class ChatForm(forms.Form):
    text_field_attrs = {
        'id': "input-field",
        'class': "input-field",
        'placeholder': _('Type your message here...')
    }

    text_field = forms.CharField(label="",
                                 widget=forms.TextInput(attrs=text_field_attrs))


class ProviderLoginForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.provider_fields = kwargs.pop('provider_fields', [])
        super(ProviderLoginForm, self).__init__(*args, **kwargs)

        for field in self.provider_fields:
            text_field_attrs = {
                'name': field['name'],
                'class': "input-field",
                'placeholder': field['label']
            }

            widget = forms.PasswordInput(attrs=text_field_attrs) if field['type'] == 'password' \
                else forms.TextInput(attrs=text_field_attrs)

            self.fields[field['name']] = forms.CharField(label="",
                                                         widget=widget)
