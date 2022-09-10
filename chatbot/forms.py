from django import forms


class LoginForm(forms.Form):
    attrs = {
        'placeholder': 'API key'
    }

    api_key = forms.CharField(label="",
                              widget=forms.TextInput(attrs=attrs))
