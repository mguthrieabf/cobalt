from django.urls import path
from . import views

urlpatterns = [
    path('', views.post_list, name='forums'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/new/', views.post_new, name='post_new'),
    path('post/like-post/<int:pk>/', views.like_post, name='like_post'),
    path('post/like-comment1/<int:pk>/', views.like_comment1, name='like_comment1'),
    path('post/like-comment2/<int:pk>/', views.like_comment2, name='like_comment2'),
]
