from django import forms
from django.utils.translation import gettext_lazy as _


class LoginForm(forms.Form):
    attrs = {
        'id': "input-field",
        'placeholder': 'API key'
    }

    api_key = forms.CharField(label="",
                              widget=forms.TextInput(attrs=attrs))


class ChatForm(forms.Form):
    text_field_attrs = {
        'id': "input-field",
        'placeholder': _('Type your message here...')
    }

    text_field = forms.CharField(label="",
                                 widget=forms.TextInput(attrs=text_field_attrs))
