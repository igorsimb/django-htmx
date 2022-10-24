from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.views.generic import FormView, TemplateView, ListView
from django.contrib.auth import get_user_model

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.paginator import Paginator

from films.forms import RegisterForm
from films.models import Film, UserFilms
from films.utils import get_max_order, reorder


class IndexView(TemplateView):
    template_name = 'index.html'


class Login(LoginView):
    template_name = 'registration/login.html'


class RegisterView(FormView):
    form_class = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        form.save()  # save the user
        return super().form_valid(form)


def check_username(request):
    username = request.POST.get('username')
    # if username from the form matches a username in our database
    if get_user_model().objects.filter(username=username).exists():
        # we keep the id but we change the class (see static/css/styles.css)
        return HttpResponse('<div id="username-err" class="registration_error">This username already exists.</div>')
    else:
        return HttpResponse('<div id="username-err" class="registration_success">This username is available.</div>')


class FilmList(LoginRequiredMixin, ListView):
    model = UserFilms
    template_name = "films.html"
    context_object_name = "films"
    # can be used with HTMX infinite scroll https://htmx.org/examples/infinite-scroll/
    paginate_by = settings.PAGINATE_BY

    def get_template_names(self):
        # pip install django_htmx
        # Source: https://django-htmx.readthedocs.io/en/latest/tips.html
        if self.request.htmx:  # if request comes from HTMX
            return 'partials/film-list-elements.html.'
        return 'films.html'

    def get_queryset(self):
        return UserFilms.objects.prefetch_related('films').filter(user=self.request.user)


@login_required
def add_film(request):
    name = request.POST.get("filmname")  # input name from films.html:10

    # if film exists, get it from db; if it doesn't - create a new one in db
    # get_or_create returns a tuple (object, created (boolean)), so we use "film, create"
    film, created = Film.objects.get_or_create(name=name)  # OR film = Film.objects.get_or_create(name=name)[0]

    # add the film to the user's list
    # if we don't have a film with this name for this user, create one
    if not UserFilms.objects.filter(films=film, user=request.user).exists():
        UserFilms.objects.create(
            films=film,
            user=request.user,
            order=get_max_order(request.user))

    # return template with all of the user's films
    films = UserFilms.objects.filter(user=request.user)
    messages.success(request, f'Added "{name}" to the list of films')
    return render(request, "partials/film-list.html", {'films': films})


@login_required
@require_http_methods('DELETE')  # allow only DELETE http requests (not PUT or POST) - for security
def delete_film(request, pk):
    userfilm = UserFilms.objects.get(pk=pk)
    # remove the film from the user's list
    UserFilms.objects.get(pk=pk).delete()
    reorder(request.user)

    # return the template fragment
    films = UserFilms.objects.filter(user=request.user)
    messages.error(request, f'Deleted "{userfilm.films}" from the list of films')
    return render(request, "partials/film-list.html", {'films': films})


def search_film(request):
    search_text = request.POST.get('search')  # what user typed into the search field

    # look up all films that containt the text
    # exclude user films
    userfilms = UserFilms.objects.filter(user=request.user)  # all films that user added (left list)
    results = Film.objects.filter(name__icontains=search_text).exclude(
        name__in=userfilms.values_list('films__name', flat=True)
    )
    context = {'results': results}
    return render(request, "partials/search-results.html", context)


def clear(request):
    return HttpResponse("")


def sort(request):
    # we need to accept request from sortable.js
    # film_order comes from film-list.html: <input type="hidden" name="film_order" value="{{ film.pk }}">
    films_pks_order = request.POST.getlist('film_order')
    films = []
    updated_films = []

    # fetch user's films in advance (rather than once per loop)
    userfilms = UserFilms.objects.prefetch_related('films').filter(user=request.user)

    for idx, film_pk in enumerate(films_pks_order, start=1):
        # userfilm = UserFilms.objects.get(pk=film_pk)

        # find instance w/ the correct PK
        userfilm = next(u for u in userfilms if u.pk == int(film_pk))

        # add changed movies only to an updated_films list
        # e.g. if we move film #1 to spot #5, only films #1-#5 will update order, instead of ALL of them
        # it saves time considerably
        if userfilm.order != idx:
            userfilm.order = idx
            updated_films.append(userfilm)
        films.append(userfilm)

    # bulk_update changed UserFilms's 'order' field
    UserFilms.objects.bulk_update(updated_films, ['order'])

    paginator = Paginator(films, settings.PAGINATE_BY)
    page_number = len(films_pks_order) / settings.PAGINATE_BY
    page_obj = paginator.get_page(page_number)
    context = {'films': films, 'page_obj': page_obj}

    return render(request, "partials/film-list.html", context)


@login_required
def detail(request, pk):
    userfilm = get_object_or_404(UserFilms, pk=pk)
    context = {'userfilm': userfilm}
    return render(request, 'partials/film-detail.html', context)


@login_required
def films_partial(request):
    films = UserFilms.objects.filter(user=request.user)
    return render(request, 'partials/film-list.html', {'films': films})


def upload_photo(request, pk):
    userfilm = get_object_or_404(UserFilms, pk=pk)
    print(request.FILES)
    photo = request.FILES.get('photo')  # <input type="file" name="photo"> in film-detail.html
    userfilm.films.photo.save(photo.name, photo)
    context = {'userfilm': userfilm}
    return render(request, 'partials/film-detail.html', context)
