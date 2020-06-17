from django.conf import settings
from django.db import models
from django.utils import timezone


class Forum(models.Model):
    title = models.CharField("Forum Short Title", max_length=80)
    description = models.CharField("Forum Description", max_length=200)

    def __str__(self):
        return self.title


class AbstractForum(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    last_change_date = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class Post(AbstractForum):
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    summary = models.TextField()
    text = models.TextField()

    def __str__(self):
        return self.title


class Comment1(AbstractForum):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return "%s - comment by %s" % (self.post.title, self.author.full_name)


class Comment2(AbstractForum):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    comment1 = models.ForeignKey(Comment1, on_delete=models.CASCADE)
    text = models.TextField()


class AbstractLike(models.Model):
    liker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class LikePost(AbstractLike):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)


class LikeComment1(AbstractLike):
    comment1 = models.ForeignKey(Comment1, on_delete=models.CASCADE)


class LikeComment2(AbstractLike):
    comment2 = models.ForeignKey(Comment2, on_delete=models.CASCADE)


# class UserForumRole(models.Model):
#     ROLE_TYPE = [
#         ('Poster', 'Poster - can create a new post'),
#         ('Responder', 'Responder - can reply to a post'),
#         ('Moderator', 'Moderator - can manage the forum'),
#     ]
#     RULE_TYPE = [
#         ('Allow', 'Allows a user to perform a role'),
#         ('Block', 'Blocks a user from performing a role')
#     ]
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     forum = models.ForeignKey(Forum, on_delete=models.CASCADE)
#     role = models.CharField("User role in forum", choices = ROLE_TYPE, max_length=20)
#     rule = models.CharField("Type of Rule", choices = RULE_TYPE, max_length=5)
#
#     def get_forums_post_allowed(user):
#         ufr = UserForumRole.objects.filter(user=user).filter(role='Poster').filter(rule='Allow').values('forum')
#         return ufr
