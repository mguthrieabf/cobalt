from django import forms
from .models import Post, Comment1
from django_summernote.widgets import SummernoteWidget, SummernoteInplaceWidget

class PostForm(forms.ModelForm):
    summary = forms.CharField(widget=SummernoteInplaceWidget(attrs={
    'summernote': {
            'placeholder': '<br>Enter a short description. Keep it punchy, this goes on the front page. Use it to tempt your reader.',
             'height': 200}}))
    text = forms.CharField(widget=SummernoteInplaceWidget(attrs={'summernote': {
            'placeholder': '<br><br>Write your article. Start typing!'}}))

    class Meta:
        model = Post
        fields = ('forum', 'title', 'summary', 'text', )

class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment1
        fields = ('text', 'post',)
