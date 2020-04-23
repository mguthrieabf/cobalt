from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import login, authenticate
from .models import User
from .forms import UserRegisterForm
from .tokens import account_activation_token
from cobalt.settings import DEFAULT_FROM_EMAIL
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse


def register(request):
    if request.method == 'POST':
        # request is immutable so copy it and add in username
        # request.POST = request.POST.copy()
        # request.POST['username'] = request.POST['abf_number']
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False   # not active until email confirmed
            user.abf_number = user.username
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activate your account.'
            message = render_to_string('accounts/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'token':account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            send_mail(mail_subject, message, DEFAULT_FROM_EMAIL, [to_email], fail_silently=False)
            return render(request, 'accounts/register_complete.html', {'email_address' : to_email})
    else:
        form = UserRegisterForm()

    print(form.errors)

    return render(request, 'accounts/register.html', {'user_form': form})

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return render(request, 'accounts/activate_complete.html', { 'user' : user})
    else:
        return HttpResponse('Activation link is invalid!')

def loggedout(request):
    return render(request, 'accounts/loggedout.html')

@login_required(login_url='/accounts/login/')
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {
        'form': form
    })

@login_required(login_url='/accounts/login/')
def search(request):

    msg=""

    if request.method == "GET":

        if 'lastname' in request.GET:
            search_last_name = request.GET.get("lastname")
        else:
            search_last_name = None

        if 'firstname' in request.GET:
            search_first_name = request.GET.get("firstname")
        else:
            search_first_name = None

        if search_first_name and search_last_name:
            members = User.objects.filter(first_name__istartswith=search_first_name, last_name__istartswith=search_last_name)
        elif search_last_name:
            members = User.objects.filter(last_name__istartswith=search_last_name)
        else:
            members = User.objects.filter(first_name__istartswith=search_first_name)

        if request.is_ajax:
            if members.count()>30:
                msg="Too many results (%s)" % members.count()
                members=None
            html = render_to_string(
                template_name="accounts/search-results.html",
                context={"members": members, "msg": msg}
            )

            data_dict = {"data": html}

            return JsonResponse(data=data_dict, safe=False)

    return render(request, "accounts/search-results.html", context={'members': members})
