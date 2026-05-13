"""Model form used by the chat composer partial."""

from django import forms
from .models import Messages

class MessageForm(forms.ModelForm):
    """Minimal form capturing only the message body."""

    class Meta:
        model = Messages
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Napisz wiadomość...'})
        }