""" Views for Forums """

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import timezone
from django.template.loader import render_to_string
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from rbac.core import rbac_user_blocked_for_model, rbac_user_has_role
from notifications.views import notify_happening
from .forms import PostForm, CommentForm, Comment2Form
from .models import (
    Post,
    Comment1,
    Comment2,
    LikePost,
    LikeComment1,
    LikeComment2,
    Forum,
    ForumFollow,
)


@login_required()
def post_list(request, forum_list=None, short_view=False):
    """ Summary view showing a list of posts.

    Args:
        request(HTTPRequest): standard user request
        forum_list(list): list of forums to include (Optional)
        short_view(Boolean): Flag for long or short view

    Returns:
        page(HTTPResponse): page with list of posts
    """

    # get list of forums user cannot access
    blocked = rbac_user_blocked_for_model(
        user=request.user, app="forums", model="forum", action="view"
    )

    # if we got a forum list then remove anything blocked
    if forum_list:
        forum_list_allowed = [item for item in forum_list if item not in blocked]
        posts_list = Post.objects.filter(forum__in=forum_list_allowed).order_by(
            "-created_date"
        )

    # Otherwise load everything not blocked
    else:
        posts_list = Post.objects.exclude(forum__in=blocked).order_by("-created_date")

    # handle pagination
    page = request.GET.get("page", 1)
    paginator = Paginator(posts_list, 10)
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    #    print(posts)

    # TODO: fix counts on paginated pages - doesn't work with posts_new
    posts_new = []
    for post in posts:
        post.post_comments = Comment1.objects.filter(post=post).count()
        post.post_comments += Comment2.objects.filter(post=post).count()
        posts_new.append(post)

    #    print(posts_new)

    if short_view:
        return render(request, "forums/post_list_short.html", {"posts": posts})
    else:
        return render(request, "forums/post_list.html", {"posts": posts})


def post_list_single_forum(request, forum_id):
    """ Front for post_list provides single forum view

    Args:
        request(HTTPRequest): standard user request
        forum_id(int): forum to view

    Returns:
        page(HTTPResponse): page with list of posts
    """

    return post_list(request, forum_list=[forum_id])


def post_list_short_view(request):
    """ Front for post_list provides compact listing

    Args:
        request(HTTPRequest): standard user request

    Returns:
        page(HTTPResponse): page with list of posts
    """

    return post_list(request, short_view=True)


@login_required()
def post_list_dashboard(request):
    """ Summary view showing a list of posts for use by the dashboard.

    Args:
        request(HTTPRequest): standard user request

    Returns:
        list:   list of Post objects
    """

    # get list of forums user cannot access
    blocked = rbac_user_blocked_for_model(
        user=request.user, app="forums", model="forum", action="view"
    )

    posts = Post.objects.exclude(forum__in=blocked).order_by("-created_date")[:20]
    posts_new = []
    for post in posts:
        post.post_comments = Comment1.objects.filter(post=post).count()
        post.post_comments += Comment2.objects.filter(post=post).count()
        posts_new.append(post)

    return posts_new


@login_required()
def post_detail(request, pk):
    """ Main view for existing post.

    Shows post and existing comments and allows the user to coment at either
    level (Comment1 or Comment2).

    Args:
        request(HTTPRequest): standard request object
        pk(int):    primary key of post

    Returns:
        HTTPResponse
    """

    # Check access
    post = get_object_or_404(Post, pk=pk)
    if not rbac_user_has_role(request.user, "forums.forum.%s.view" % post.forum.id):
        return HttpResponseForbidden()

    if request.method == "POST":
        # identify which form submitted this - comments1 or comments2
        if "submit-c1" in request.POST:
            form = CommentForm(request.POST)
        elif "submit-c2" in request.POST:
            form = Comment2Form(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            # Tell people
            notify_happening(
                application_name="Forums",
                event_type="forums.post.comment",
                msg="%s commented on your post: %s" % (request.user, post.post.title),
                topic=post.post.id,
            )
        else:
            print(form.errors)
    form = CommentForm()
    form2 = Comment2Form()
    post = get_object_or_404(Post, pk=pk)
    post_likes = LikePost.objects.filter(post=post)
    comments1 = Comment1.objects.filter(post=post)

    total_comments = 0
    comments1_new = []  # comments1 is immutable - make a copy
    for c1 in comments1:
        # add related c2 objects to c1
        c2 = Comment2.objects.filter(comment1=c1)
        c2_new = []
        for i in c2:
            i.c2_likes = LikeComment2.objects.filter(comment2=i).count()
            c2_new.append(i)
        c1.c2 = c2_new
        # number of comments
        total_comments += 1
        total_comments += len(c1.c2)
        # number of likes
        c1.c1_likes = LikeComment1.objects.filter(comment1=c1).count()
        comments1_new.append(c1)

    return render(
        request,
        "forums/post_detail.html",
        {
            "form": form,
            "form2": form2,
            "post": post,
            "comments1": comments1_new,
            "post_likes": post_likes,
            "total_comments": total_comments,
        },
    )


@login_required()
def post_new(request):
    """ Create a new post in a forum """

    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            if rbac_user_has_role(
                request.user, "forums.forum.%s.create" % form.cleaned_data["forum"].id
            ):
                post = form.save(commit=False)
                post.author = request.user
                post.published_date = timezone.now()
                post.save()

                link = reverse("forums:post_detail", args=[post.id])
                host = request.get_host()
                absolute_link = "http://%s%s" % (host, link)

                email_body = "%s created a new post in %s called '%s.'" % (
                    post.author,
                    post.forum.title,
                    post.title,
                )

                context = {
                    "title": "New Post: %s" % post.title,
                    "email_body": email_body,
                    "absolute_link": absolute_link,
                    "host": host,
                    "link_text": "See Post",
                }

                html_msg = render_to_string(
                    "notifications/email-notification.html", context
                )

                msg = "New Post %s by %s" % (post.title, post.author)

                email_subject = "New Post in Forum: %s" % post.forum.title

                # Tell people
                notify_happening(
                    application_name="Forums",
                    event_type="forums.post.create",
                    msg=msg,
                    html_msg=html_msg,
                    topic=post.forum.id,
                    link=link,
                    email_subject=email_subject,
                )

                # notify user of comments
                # create_user_notification(
                #     member=post.author,
                #     application_name="Forums",
                #     event_type="forums.post.comment",
                #     topic=post.id,
                #     notification_type="Email",
                # )

                return redirect("forums:post_detail", pk=post.pk)
            else:
                return HttpResponseForbidden()

    else:
        # see which forums are blocked for this user - load a list of the others
        blocked_forums = rbac_user_blocked_for_model(
            user=request.user, app="forums", model="forum", action="create"
        )
        valid_forums = Forum.objects.exclude(id__in=blocked_forums)
        form = PostForm(valid_forums=valid_forums)

    return render(request, "forums/post_edit.html", {"form": form, "request": request})


@login_required()
def post_edit(request, post_id):
    """ Edit a post in a forum """

    post = get_object_or_404(Post, pk=post_id)

    if request.method == "POST":
        if "publish" in request.POST:  # Publish
            form = PostForm(request.POST, instance=post)
            if form.is_valid():
                if (
                    rbac_user_has_role(
                        request.user,
                        "forums.forum.%s.create" % form.cleaned_data["forum"].id,
                    )
                    and post.author == request.user
                ):
                    post = form.save(commit=False)
                    post.last_change_date = timezone.now()
                    post.save()
                    messages.success(
                        request, "Post created", extra_tags="cobalt-message-success"
                    )
                    return redirect("forums:post_detail", pk=post.pk)
                else:
                    return HttpResponseForbidden()

        elif "delete" in request.POST:  # Delete
            post.delete()
            messages.success(
                request, "Post deleted", extra_tags="cobalt-message-success"
            )
            return redirect("forums:forums")

        else:  # Maybe cancel hit or back button - reload page
            return redirect("forums:post_edit", post_id=post_id)
    else:
        if request.user != post.author:
            return HttpResponseForbidden()

        # see which forums are blocked for this user - load a list of the others
        blocked_forums = rbac_user_blocked_for_model(
            user=request.user, app="forums", model="forum", action="create"
        )
        valid_forums = Forum.objects.exclude(id__in=blocked_forums)
        form = PostForm(valid_forums=valid_forums, instance=post)

    return render(
        request,
        "forums/post_edit.html",
        {"form": form, "request": request, "edit": True},
    )


@login_required()
def like_post(request, pk):
    """ Function to like a post over ajax

    Args:
        request(HTTPRequest): standard request object
        pk(int):    Primary key of the post to like

    Returns:
        HttpResponse
    """

    if request.method == "POST":
        already_liked = LikePost.objects.filter(post=pk, liker=request.user)
        if not already_liked:
            like = LikePost()
            like.liker = request.user
            like.post = Post.objects.get(pk=pk)
            like.save()
            return HttpResponse("ok")
        else:
            return HttpResponse("already liked")
    return HttpResponse("Invalid request")


@login_required()
def like_comment1(request, pk):
    """ Function to like a comment1 over ajax

    Args:
        request(HTTPRequest): standard request object
        pk(int):    Primary key of the comment1 to like

    Returns:
        HttpResponse
    """
    if request.method == "POST":
        already_liked = LikeComment1.objects.filter(comment1=pk, liker=request.user)
        if not already_liked:
            like = LikeComment1()
            like.liker = request.user
            like.comment1 = Comment1.objects.get(pk=pk)
            like.save()
            return HttpResponse("ok")
        else:
            return HttpResponse("already liked")
    return HttpResponse("Invalid request")


@login_required()
def like_comment2(request, pk):
    """ Function to like a comment2 over ajax

    Args:
        request(HTTPRequest): standard request object
        pk(int):    Primary key of the comment2 to like

    Returns:
        HttpResponse
    """

    if request.method == "POST":
        already_liked = LikeComment2.objects.filter(comment2=pk, liker=request.user)
        if not already_liked:
            like = LikeComment2()
            like.liker = request.user
            like.comment2 = Comment2.objects.get(pk=pk)
            like.save()
            return HttpResponse("ok")
        else:
            return HttpResponse("already liked")
    return HttpResponse("Invalid request")


@login_required
def forum_list(request):
    """ View to show a list of forums """

    forums = Forum.objects.all()
    forums_all = []

    forum_follows = list(
        ForumFollow.objects.filter(user=request.user).values_list("forum")
    )

    print(forum_follows)

    for forum in forums:
        detail = {}
        count = Post.objects.filter(forum=forum).count()
        if count != 0:
            latest_post = Post.objects.filter(forum=forum).latest("created_date")
            latest_author = latest_post.author
            latest_title = latest_post.title
            latest_date = latest_post.created_date
        else:
            latest_author = ""
            latest_title = "No posts yet"
            latest_date = ""

        detail["id"] = forum.id
        detail["title"] = forum.title
        detail["description"] = forum.description
        detail["count"] = count
        detail["latest_author"] = latest_author
        detail["latest_title"] = latest_title
        detail["latest_date"] = latest_date
        if (forum.id,) in forum_follows:  # there maybe a nicer way to unpack this
            detail["follows"] = True
        else:
            detail["follows"] = False
        forums_all.append(detail)

    return render(request, "forums/forum_list.html", {"forums": forums_all})
