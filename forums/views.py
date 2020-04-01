from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from .models import Post, Comment1, Comment2, LikePost, LikeComment1, LikeComment2
from .forms import PostForm

@login_required(login_url='/accounts/login/')
def home(request):
    return render(request, 'forums/home.html')

@login_required(login_url='/accounts/login/')
def post_list(request):
#    posts=Post.objects.all()
    posts = Post.objects.all().order_by('-created_date')
    return render(request, 'forums/post_list.html', {'posts' : posts})

@login_required(login_url='/accounts/login/')
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post_likes = LikePost.objects.filter(post = post)
    comments1 = Comment1.objects.filter(post = post)

    total_comments = 0
    comments1_new = [] # comments1 is immutable - make a copy
    for c1 in comments1:
        total_comments += 1
        c1.c2 = Comment2.objects.filter(comment1 = c1)
        total_comments += len(c1.c2)
        comments1_new.append(c1)

    return render(request, 'forums/post_detail.html', {'post': post,
                                                       'comments1' : comments1_new,
                                                       'post_likes' : post_likes,
                                                       'total_comments' : total_comments})

@login_required(login_url='/accounts/login/')
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
    return render(request, 'forums/post_edit.html', {'form': form, 'request': request})
