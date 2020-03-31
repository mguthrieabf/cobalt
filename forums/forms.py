from django import forms
from .models import Post
from django_summernote.widgets import SummernoteWidget, SummernoteInplaceWidget

class PostForm(forms.ModelForm):
    text = forms.CharField(widget=SummernoteWidget)
#     text = forms.CharField(widget=SummernoteWidget(attrs={'summernote': {
#
# 'height': 100,
#   'toolbar': false,
#   'placeholder': 'type with apple, orange, watermelon and lemon',
#   hint: {
#     words: ['apple', 'orange', 'watermelon', 'lemon'],
#     match: \/\b(\w{1,})$\/,
#     search: function (keyword, callback) {
#       callback($.grep(this.words, function (item) {
#         return item.indexOf(keyword) === 0;
#       }));
#     }
#   }
# });


    # }}))
    class Meta:
        model = Post
        fields = ('forum', 'title', 'text', )
        widgets = { 'text' : SummernoteWidget() }
