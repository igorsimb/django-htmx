from django.db.models import Max
from films.models import UserFilms


def get_max_order(user) -> int:
    """
    Default order function. Sends newly added film to the end of the order line.
    """
    # all user's films
    existing_films = UserFilms.objects.filter(user=user)
    if not existing_films.exists():
        # if no movies in user's list, the first film's order should be #1
        return 1
    else:
        # go through all user's films, find the maximum and return maximum + 1
        current_max = existing_films.aggregate(max_order=Max('order'))['max_order']
        return current_max + 1


def reorder(user):
    """
    Reorder other films after deleting a film
    """
    existing_films = UserFilms.objects.filter(user=user)
    if not existing_films.exists():
        return
    number_of_films = existing_films.count()
    new_ordering = range(1, number_of_films + 1)

    for order, user_film in zip(new_ordering, existing_films):
        user_film.order = order
        user_film.save()
