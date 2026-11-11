from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(max_length=120, widget=forms.TextInput(attrs={"class": "at-field__input", "autocomplete": "name"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "at-field__input", "autocomplete": "email"}))
    message = forms.CharField(max_length=5000, widget=forms.Textarea(attrs={"class": "at-field__input", "rows": 6}))
    # Honeypot: hidden from people, filled in by bots. Must stay empty.
    website = forms.CharField(required=False, label="Website",
                              widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))
