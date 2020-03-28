from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from accounts.forms import UserUpdateForm


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
        print(request.user.dob)
        request.user.dob=request.user.dob.strftime("%d/%m/%Y")
        print(request.user.dob)

        form = UserUpdateForm(instance=request.user)

# fix date format for dob
#    print(form['dob'])
#    form['dob']="03/05/1967"

    context = {
        'form': form,
        'msg': msg,
    }
    return render(request, 'user_profile/home.html', context)
