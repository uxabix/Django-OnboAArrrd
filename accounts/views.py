from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def home(request):
    return render(request, "accounts/home.html")


@login_required
def logged(request):
    return render(request, "accounts/logged.html")

