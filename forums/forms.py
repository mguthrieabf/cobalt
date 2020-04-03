from django import forms
from .models import Post
from django_summernote.widgets import SummernoteWidget, SummernoteInplaceWidget

class PostForm(forms.ModelForm):
    summary = forms.CharField(widget=SummernoteInplaceWidget(attrs={
    'summernote': {
            'placeholder': '<br><br>Short description. Keep it punchy.',
             'height': 200}}))
    text = forms.CharField(widget=SummernoteInplaceWidget(attrs={'summernote': {
            'placeholder': '<br><br>Start typing...'}}))

    class Meta:
        model = Post
        fields = ('forum', 'title', 'summary', 'text', )
#        widgets = { 'text' : SummernoteInplaceWidget() }
