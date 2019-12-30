from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from .forms import UserRegisterForm, ProfileRegisterForm

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        p_reg_form = ProfileRegisterForm(request.POST)
        if form.is_valid() and p_reg_form.is_valid():
            user = form.save()
            user.refresh_from_db()  # load the profile instance created by the signal
            p_reg_form = ProfileRegisterForm(request.POST, instance=user.profile)
            p_reg_form.full_clean()
            p_reg_form.save()
            return redirect('login')
    else:
        form = UserRegisterForm()
        p_reg_form = ProfileRegisterForm()
    context = {
        'user_form': form,
        'profile_form': p_reg_form
    }
    return render(request, 'accounts/register.html', context)

def loggedout(request):
    return render(request, 'accounts/loggedout.html')
