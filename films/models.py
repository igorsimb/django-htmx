from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.functions import Lower


class User(AbstractUser):
    pass


class Film(models.Model):
    name = models.CharField(max_length=128, unique=True)

    # problem: Django migration error: you cannot alter to or from M2M fields, or add or remove through= on M2M fields
    # Solution:
    # must migrate, and THEN put through="UserFilms", try to migrate - you get an error; do the following:
    # Source: https://stackoverflow.com/questions/26927705/django-migration-error-you-cannot-alter-to-or-from-m2m-fields-or-add-or-remove

    # tldr:
    # 1. go to migrations -> alter_film_users
    # 2. change AlterField to RemoveField
    # 3. remove this line `field=models.ManyToManyField(related_name='films', through='films.UserFilms', to=settings.AUTH_USER_MODEL),`
    # 4. add the following to the operations list:
    #     migrations.AddField(
    #         model_name='film',
    #         name='users',
    #         field=models.ManyToManyField(related_name='films', through='films.UserFilms', to=settings.AUTH_USER_MODEL),
    #     ),
    # 5. Migrate
    users = models.ManyToManyField(User, related_name="films", through="UserFilms")  # user.films.all()
    photo = models.ImageField(upload_to='film_photos/', null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = [Lower('name')]


class UserFilms(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    films = models.ForeignKey(Film, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField()  # values from 0 to 32767

    class Meta:
        ordering = ['order']