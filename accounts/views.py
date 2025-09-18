from django.contrib.auth import authenticate
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.http import HttpResponse

# Create your views here.
def custom_login_view(request):

    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)

    return redirect('home')

def custom_logout_view(request,):
    logout(request)
    return redirect('home')




def profile_view(request):
    return HttpResponse('ProfileView')

def create_user_view(request):
    return HttpResponse('create_user View')