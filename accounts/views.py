from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def home(request):
    return render(request, 'home.html')

@login_required
def logged(request):
    # request.user to instancja CustomUser
    return render(request, 'logged.html')
