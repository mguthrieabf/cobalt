from django import forms
from .models import Post
from django_summernote.widgets import SummernoteWidget, SummernoteInplaceWidget

class PostForm(forms.ModelForm):
    text = forms.CharField(widget=SummernoteWidget)

    class Meta:
        model = Post
        fields = ('forum', 'title', 'text', )
        widgets = { 'text' : SummernoteWidget() }
