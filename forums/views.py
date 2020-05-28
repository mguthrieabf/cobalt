from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from .models import Post, Comment1, Comment2, LikePost, LikeComment1, LikeComment2
from .forms import PostForm, CommentForm, Comment2Form
from notifications.views import notify_happening, create_user_notification
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required()
def post_list(request):
    posts_list = Post.objects.all().order_by('-created_date')
    page = request.GET.get('page', 1)
    paginator = Paginator(posts_list, 10)
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    posts_new=[]
    for p in posts:
        p.post_comments = Comment1.objects.filter(post = p).count()
        p.post_comments += Comment2.objects.filter(post = p).count()
        posts_new.append(p)

    return render(request, 'forums/post_list.html', {'posts' : posts_new})

@login_required()
def post_list_dashboard(request):
    posts = Post.objects.all().order_by('-created_date')[:20]
    posts_new=[]
    for p in posts:
        p.post_comments = Comment1.objects.filter(post = p).count()
        p.post_comments += Comment2.objects.filter(post = p).count()
        posts_new.append(p)

    return posts_new

@login_required()
def post_detail(request, pk):
    if request.method == "POST":
# identify which form submitted this - comments1 or comments2
        if 'submit-c1' in request.POST:
            form = CommentForm(request.POST)
        elif 'submit-c2' in request.POST:
            form = Comment2Form(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
# Tell people
            notify_happening(application_name="Forums",
                             event_type="forums.post.comment",
                             msg="%s commented on your post: %s" % (request.user, post.post.title),
                             topic=post.post.id)
        else:
            print(form.errors)
    form = CommentForm()
    form2 = Comment2Form()
    post = get_object_or_404(Post, pk=pk)
    post_likes = LikePost.objects.filter(post = post)
    comments1 = Comment1.objects.filter(post = post)

    total_comments = 0
    comments1_new = [] # comments1 is immutable - make a copy
    for c1 in comments1:
# add related c2 objects to c1
        c2 = Comment2.objects.filter(comment1 = c1)
        c2_new = []
        for i in c2:
            i.c2_likes = LikeComment2.objects.filter(comment2 = i).count()
            c2_new.append(i)
        c1.c2 = c2_new
# number of comments
        total_comments += 1
        total_comments += len(c1.c2)
# number of likes
        c1.c1_likes = LikeComment1.objects.filter(comment1 = c1).count()
        comments1_new.append(c1)

    return render(request, 'forums/post_detail.html', {'form': form,
                                                       'form2': form2,
                                                       'post': post,
                                                       'comments1' : comments1_new,
                                                       'post_likes' : post_likes,
                                                       'total_comments' : total_comments})

@login_required()
def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()
            post.save()
            notifymsg = "New post to Forum %s by %s Titled %s" % (post.forum,
                                                               post.author,
                                                               post.title)

# Tell people
            notify_happening(application_name="Forums",
                             event_type="forums.post.new",
                             msg=notifymsg,
                             topic=post.forum.id)
# notify user of comments
            create_user_notification(member=post.author,
                                     application_name="Forums",
                                     event_type="forums.post.comment",
                                     topic=post.id,
                                     notification_type="Email")

            return redirect('forums:post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'forums/post_edit.html', {'form': form, 'request': request})

@login_required()
def like_post(request, pk):
    if request.method == "POST":
        already_liked = LikePost.objects.filter(post=pk, liker=request.user)
        if not already_liked:
            like=LikePost()
            like.liker=request.user
            like.post=Post.objects.get(pk=pk)
            like.save()
            return HttpResponse("ok")
        else:
            return HttpResponse("already liked")

@login_required()
def like_comment1(request, pk):
    if request.method == "POST":
        already_liked = LikeComment1.objects.filter(comment1=pk, liker=request.user)
        if not already_liked:
            like=LikeComment1()
            like.liker=request.user
            like.comment1=Comment1.objects.get(pk=pk)
            like.save()
            return HttpResponse("ok")
        else:
            return HttpResponse("already liked")

@login_required()
def like_comment2(request, pk):
    if request.method == "POST":
        already_liked = LikeComment2.objects.filter(comment2=pk, liker=request.user)
        if not already_liked:
            like=LikeComment2()
            like.liker=request.user
            like.comment2=Comment2.objects.get(pk=pk)
            like.save()
            return HttpResponse("ok")
        else:
            return HttpResponse("already liked")
