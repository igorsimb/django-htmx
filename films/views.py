from django.http.response import HttpResponse, HttpResponsePermanentRedirect
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.views.generic import FormView, TemplateView, ListView
from django.contrib.auth import get_user_model

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_http_methods
from django.contrib import messages

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
    model = Film
    template_name = "films.html"
    context_object_name = "films"

    def get_queryset(self):
        return UserFilms.objects.filter(user=self.request.user)



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
    userfilms = UserFilms.objects.filter(user=request.user) # all films that user added (left list)
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
    for idx, film_pk in enumerate(films_pks_order, start=1):
        userfilm = UserFilms.objects.get(pk=film_pk)
        userfilm.order = idx
        userfilm.save()
        films.append(userfilm)

    return render(request, "partials/film-list.html", {'films': films})