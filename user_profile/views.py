from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from accounts.forms import UserRegisterForm

@login_required
def home(request):
    if request.method == 'POST':
        form = UserRegisterForm(data=request.POST, instance=request.user)
        if form.is_valid():
        #     user = form.save(commit=False)
        #     user.is_active = False   # not active until email confirmed
        #     user.save()
            print("later")
        else:
            print("Not valid")
        u=request.user
        print(u)
        print(u.first_name)
        u.first_name="Fred"
        u.save()
    else:
        user=request.user
        form = UserRegisterForm(instance=user)
        context = {
            'form': form,
        }
        return render(request, 'user_profile/home.html', context)
