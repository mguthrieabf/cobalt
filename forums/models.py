""" Models for Forums """
from django.conf import settings
from django.db import models
from django.utils import timezone


class Forum(models.Model):
    """ Forum is a list of valid places to create a Post """

    title = models.CharField("Forum Short Title", max_length=80)
    description = models.CharField("Forum Description", max_length=200)

    def __str__(self):
        return self.title


class AbstractForum(models.Model):
    """ Lots of things have the same attributes so use an Abstract Class """

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    last_change_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        """ We are abstract """

        abstract = True


class Post(AbstractForum):
    """ A Post is the highest level thing in Forums """

    forum = models.ForeignKey(Forum, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    summary = models.TextField()
    text = models.TextField()

    def __str__(self):
        return self.title


class Comment1(AbstractForum):
    """ First level comments """

    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return "%s - comment by %s" % (self.post.title, self.author.full_name)


class Comment2(AbstractForum):
    """ Second level comments """

    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    comment1 = models.ForeignKey(Comment1, on_delete=models.CASCADE)
    text = models.TextField()


class AbstractLike(models.Model):
    """ Abstract for likes """

    liker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        """ We are abstract """

        abstract = True


class LikePost(AbstractLike):
    """ Like for a post """

    post = models.ForeignKey(Post, on_delete=models.CASCADE)


class LikeComment1(AbstractLike):
    """ Like for a comment1 """

    comment1 = models.ForeignKey(Comment1, on_delete=models.CASCADE)


class LikeComment2(AbstractLike):
    """ Like for a comment2 """

    comment2 = models.ForeignKey(Comment2, on_delete=models.CASCADE)


class ForumFollow(models.Model):
    """ List of Forums that a user is subscribed to """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE)

    def __str__(self):
        return "%s-%s" % (self.user, self.forum)
