from django import forms
from .models import Post, Comment1, Comment2
from django_summernote.widgets import SummernoteWidget, SummernoteInplaceWidget
from .models import Forum

class PostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):

# Get valid forums as parameter
        valid_forums = kwargs.pop('valid_forums', None)
#
# Call super()
        super(PostForm, self).__init__(*args, **kwargs)
#
# Modify valid forums if they were passed
        if valid_forums:
            self.fields['forum'].queryset = valid_forums

# Hide the crispy labels
        self.fields['forum'].label = False
        self.fields['title'].label = False
        self.fields['summary'].label = False
        self.fields['text'].label = False

    title = forms.CharField(widget=forms.TextInput(attrs={'class': 'cobalt-min-width-100'}))
    summary = forms.CharField(widget=SummernoteInplaceWidget(attrs={
    'summernote': {
            'placeholder': '<br>Enter a short description. Keep it punchy, this goes on the front page. Use it to tempt your reader.',
             'height': 200}}))
    text = forms.CharField(widget=SummernoteInplaceWidget(attrs={'summernote': {
            'placeholder': '<br><br>Write your article. <br><br>You can enter card symbols and hand diagrams from the toolbar.'}}))

    class Meta:
        model = Post
        fields = ('forum', 'title', 'comments_allowed', 'summary', 'text', )

class CommentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Hide the crispy labels
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['text'].label = False
        self.fields['text'].widget = forms.Textarea(attrs={'rows': 10, 'cols': 80, 'class': 'cobalt-min-width-100'})


    # text = forms.CharField(widget=SummernoteInplaceWidget(attrs={
    #     'summernote': {
    #         'placeholder': '<br><br>Reply C1',
    #         'toolbar': [
    #     ['font', ['bold', 'italic', 'underline']],
    #     ['color', ['color']],
    #     ['insert', ['link', 'picture', 'hr']],
    #     ['cards', ['specialcharsspades', 'specialcharshearts', 'specialcharsdiamonds', 'specialcharsclubs', 'specialcharshand']]]}}))

    class Meta:
        model = Comment1
        fields = ('text', 'post',)

class Comment2Form(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Hide the crispy labels
        super(Comment2Form, self).__init__(*args, **kwargs)
        self.fields['text'].label = False
        self.fields['text'].widget = forms.Textarea(attrs={'rows': 10, 'cols': 80, 'class': 'cobalt-textarea'})

    #
    # text = forms.CharField(widget=SummernoteInplaceWidget(attrs={
    #     'summernote': {
    #         'placeholder': '<br><br>Reply C2',
    #         'toolbar': [
    #     ['font', ['bold', 'italic', 'underline']],
    #     ['color', ['color']],
    #     ['insert', ['link', 'picture', 'hr']],
    #     ['cards', ['specialcharsspades', 'specialcharshearts', 'specialcharsdiamonds', 'specialcharsclubs', 'specialcharshand']]]}}))

    class Meta:
        model = Comment2
        fields = ('text', 'post', 'comment1')
