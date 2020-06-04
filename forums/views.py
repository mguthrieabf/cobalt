from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import timezone
from .models import Post, Comment1, Comment2, LikePost, LikeComment1, LikeComment2, Forum
from .forms import PostForm, CommentForm, Comment2Form
from notifications.views import notify_happening, create_user_notification
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rbac.core import rbac_user_blocked_for_model, rbac_user_has_role

@login_required()
def post_list(request):
    """ Summary view showing a list of posts.

    Args:
        request(HTTPRequest): standard user request

    Returns:
        page(HTTPResponse): page with list of posts
    """

# get list of forums user cannot access
    blocked = rbac_user_blocked_for_model(user=request.user,
                                          app='forums',
                                          model='forum',
                                          action='view')

    posts_list = Post.objects.exclude(forum__in=blocked).order_by('-created_date')
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
        p.post_comments = Comment1.objects.filter(post=p).count()
        p.post_comments += Comment2.objects.filter(post=p).count()
        posts_new.append(p)

    return render(request, 'forums/post_list.html', {'posts' : posts_new})

@login_required()
def post_list_dashboard(request):
    """ Summary view showing a list of posts for use by the dashboard.

    Args:
        request(HTTPRequest): standard user request

    Returns:
        list:   list of Post objects
    """

# get list of forums user cannot access
    blocked = rbac_user_blocked_for_model(user=request.user,
                                          app='forums',
                                          model='forum',
                                          action='view')

    posts = Post.objects.exclude(forum__in=blocked).order_by('-created_date')[:20]
    posts_new=[]
    for p in posts:
        p.post_comments = Comment1.objects.filter(post=p).count()
        p.post_comments += Comment2.objects.filter(post=p).count()
        posts_new.append(p)

    return posts_new

@login_required()
def post_detail(request, pk):

    post = get_object_or_404(Post, pk=pk)

    if not rbac_user_has_role(request.user, "forums.forum.%s.view" %
                     post.forum.id):
        return HttpResponseForbidden()
    else:  # access okay, continue...


        if request.method == "POST":
            if rbac_user_has_role(request.user, "forums.forum.%s.view" %
                             form.cleaned_data['forum'].id):
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
                                     msg="%s commented on post: %s" % (request.user, post.post.title),
                                     topic=post.post.id)

        form = CommentForm()
        form2 = Comment2Form()
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
    """ Create a new post in a forum """

    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            if rbac_user_has_role(request.user, "forums.forum.%s.create" %
                             form.cleaned_data['forum'].id):
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
                return HttpResponseForbidden()

    else:
# see which forums are blocked for this user - load a list of the others
        blocked_forums = rbac_user_blocked_for_model(user=request.user,
                                                     app="forums",
                                                    model="forum",
                                                    action="create")
        valid_forums = Forum.objects.exclude(id__in=blocked_forums)
        form = PostForm(valid_forums=valid_forums)

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
