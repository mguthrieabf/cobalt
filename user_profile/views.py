from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from accounts.forms import UserUpdateForm

@login_required
def home(request):
    if request.method == 'POST':
        form = UserUpdateForm(data=request.POST, instance=request.user)
        # if form.is_valid():
        #     print("later")
        # else:
        #     print("Not valid")
        #     print(form.is_valid())
        #     print(form.errors)
        u=request.user
        u.save()
        msg="Profile Updated"
    else:
        msg=""

    user=request.user
    form = UserUpdateForm(instance=user)
    context = {
        'form': form,
        'msg': msg,
    }
    return render(request, 'user_profile/home.html', context)
