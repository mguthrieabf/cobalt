from django.conf import settings
from django.db import models
from django.utils import timezone


class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    last_change_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

class Comment1(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "%s - comment by %s" % (self.post.title, self.user.username)

class Comment2(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment1 = models.ForeignKey(Comment1, on_delete=models.CASCADE)
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)

    # def __str__(self):
    #     return "%s - comment by %s - comment by %s" % (self.comment1.post.title,
    #                                                    self.comment1.user.username,
    #                                                    self.user.username)
