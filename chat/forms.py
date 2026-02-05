from django import forms
from .models import Messages

class MessageForm(forms.ModelForm):
    class Meta:
        model = Messages
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Napisz wiadomość...'})
        }