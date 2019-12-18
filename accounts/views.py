# from django.shortcuts import render, redirect
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth import authenticate, login
# from django.contrib.auth.models import User
# from django.contrib import auth
# from .forms import LoginForm
#
# from django.shortcuts import render, HttpResponseRedirect, HttpResponse
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth.models import User
# from .models import UserProfile
# from .forms import UserProfileForm
# from django.forms.models import inlineformset_factory
# from django.core.exceptions import PermissionDenied
#
# @login_required
# def edit_user(request, pk):
#     user = User.objects.get(pk=pk)
#     user_form = UserProfileForm(instance=user)
#
#     ProfileInlineFormset = inlineformset_factory(User, UserProfile, fields=('website', 'bio', 'phone', 'city', 'country', 'organization'))
#     formset = ProfileInlineFormset(instance=user)
#
#     if request.user.is_authenticated() and request.user.id == user.id:
#         if request.method == "POST":
#             user_form = UserProfileForm(request.POST, request.FILES, instance=user)
#             formset = ProfileInlineFormset(request.POST, request.FILES, instance=user)
#
#             if user_form.is_valid():
#                 created_user = user_form.save(commit=False)
#                 formset = ProfileInlineFormset(request.POST, request.FILES, instance=created_user)
#
#                 if formset.is_valid():
#                     created_user.save()
#                     formset.save()
#                     return HttpResponseRedirect('/accounts/profile/')
#
#         return render(request, "account/account_update.html", {
#             "noodle": pk,
#             "noodle_form": user_form,
#             "formset": formset,
#         })
#     else:
#         raise PermissionDenied
#
#
# #from django.views.generic import TemplateView
#
# # from .forms import ExtendedUserCreationForm
# #
# # def signup(request):
# #     if request.method == "POST":
# #         # we have received details
# #         form=ExtendedUserCreationForm(request.POST)
# #
# #         if form.is_valid():
# #             form.save()
# #
# #             username= form.cleaned_data.get('username')
# #             password = form.cleaned_data.get('password1')
# #             user=authenticate(username=username, password=password)
# #             login(request.user)
# #             return redirect('/dashboard')
# #     else:
# #         form = ExtendedUserCreationForm()
# #
# #     context = {'form' : form}
# #     return render(request, 'accounts/signup.html
# def signup2(request):
#     form = LoginForm()
#     return render(request, 'accounts/signup2.html', {'form': form})
#
# def signup(request):
#     if request.method=="POST":
#         # we have received details
#         if request.POST['password1'] == request.POST['password2']:
#             try:
#                 user=User.objects.get(username=request.POST['username'])
#                 return render(request, 'accounts/signup.html', {'error': "Username already taken."})
#             except User.DoesNotExist:
#                 user = User.objects.create_user(request.POST['username'], password=request.POST['password1'])
#                 auth.login(request, user)
#                 return redirect('home')
#         else:
#             return render(request, 'accounts/signup.html', {'error': "Passwords do not match."})
#     else:
#         # request for form only
#         return render(request, 'accounts/signup.html')
#
#
#
# def login(request):
#     if request.method=="POST":
#         user = auth.authenticate(username=request.POST['username'], password=request.POST['password'])
#         if user is not None:
#             auth.login(request, user)
#             return redirect('dashboard')
#         else:
#             return render(request, 'accounts/login.html', {'error': "Username or password incorrect."})
#     else:
#         return render(request, 'accounts/login.html')
#
# def logout(request):
#     auth.logout(request)
#     return redirect('/dashboard')
