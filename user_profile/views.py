from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from accounts.forms import UserUpdateForm, BlurbUpdateForm
from accounts.models import User

@login_required
def home(request):
    msg=""
    if request.method == 'POST':
        form = UserUpdateForm(data=request.POST, instance=request.user)
        if form.is_valid():
            msg="Profile Updated"
            print(form)
            form.save()
        else:
            print(form.errors)
    else:

# Fix DOB format for browser - expects DD/MM/YYYY
        if request.user.dob:
            request.user.dob=request.user.dob.strftime("%d/%m/%Y")

        form = UserUpdateForm(instance=request.user)
    blurbform = BlurbUpdateForm(instance=request.user)

    context = {
        'form': form,
        'blurbform': blurbform,
        'msg': msg,
    }
    return render(request, 'user_profile/home.html', context)

def blurb_form_upload(request):
    if request.method == 'POST':
        blurbform = BlurbUpdateForm(request.POST, request.FILES, instance=request.user)
        if blurbform.is_valid():
            blurbform.save()
    else:
        blurbform = BlurbUpdateForm(data=request.POST, instance=request.user)

    form = UserUpdateForm(instance=request.user)
    context = {
        'form': form,
        'blurbform': blurbform,
        'msg': "Profile Updated",
    }
    return render(request, 'user_profile/home.html', context)


@login_required
def public_profile(request, pk):
    profile = get_object_or_404(User, pk=pk)
    return render(request, 'user_profile/public_profile.html', {'profile': profile})
