from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from .models import Post, Comment1, Comment2
from .forms import PostForm

@login_required
def home(request):
    return render(request, 'forums/home.html')

def post_list(request):
    posts=Post.objects.all()
#    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
    return render(request, 'forums/post_list.html', {'posts' : posts})

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments1 = Comment1.objects.filter(post = post)
    comments2 = {}
    for c1 in comments1:
        print(c1)
        c2 = Comment2.objects.filter(comment1 = c1)
        comments2[c1]=c2
    return render(request, 'forums/post_detail.html', {'post': post, 'comments1' : comments1 })

def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'forums/post_edit.html', {'form': form})
