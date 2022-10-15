from django.http.response import HttpResponse, HttpResponsePermanentRedirect
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.views.generic import FormView, TemplateView, ListView
from django.contrib.auth import get_user_model

from films.forms import RegisterForm

from films.models import Film


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
        return HttpResponse('<div id="username-err" class="error">This username already exists.</div>')
    else:
        return HttpResponse('<div id="username-err" class="success">This username is available.</div>')


class FilmList(ListView):
    model = Film
    template_name = "films.html"
    context_object_name = "films"

    def get_queryset(self):
        user = self.request.user
        return user.films.all()


def add_film(request):
    name = request.POST.get("filmname")  # input name from films.html:10

    # if film exists, get it from db; if it doesn't - create a new one in db
    # get_or_create returns a tuple (object, created), so we use "film, create"
    film, create = Film.objects.get_or_create(name=name)

    # add the film to the user's list
    request.user.films.add(film)

    # return template with all of the user's films
    films = request.user.films.all()
    return render(request, "partials/film-list.html", {'films': films})

def delete_film(request, pk):
    # remove the film from the user's list
    request.user.films.remove(pk)

    # return the template fragment
    films = request.user.films.all()
    return render(request, "partials/film-list.html", {'films': films})