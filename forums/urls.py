from django.urls import path
from . import views

app_name = "forums"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.post_list_filter, name="forums"),
    path("post/list/", views.post_list_filter, name="post_list_filter"),
    path("post/<int:pk>/", views.post_detail, name="post_detail"),
    path(
        "forum/list/<int:forum_id>/",
        views.post_list_single_forum,
        name="post_list_single_forum",
    ),
    path("post/new/", views.post_new, name="post_new"),
    path("post/search/", views.post_search, name="post_search"),
    path("post/edit/<int:post_id>", views.post_edit, name="post_edit"),
    path("forum/list", views.forum_list, name="forum_list"),
    path("forum/create", views.forum_create, name="forum_create"),
    path("post/like-post/<int:pk>/", views.like_post, name="like_post"),
    path("post/like-comment1/<int:pk>/", views.like_comment1, name="like_comment1"),
    path("post/like-comment2/<int:pk>/", views.like_comment2, name="like_comment2"),
    path(
        "forum/follow/<int:forum_id>/",
        views.follow_forum_ajax,
        name="follow_forum_ajax",
    ),
    path(
        "forum/unfollow/<int:forum_id>/",
        views.unfollow_forum_ajax,
        name="unfollow_forum_ajax",
    ),
]
