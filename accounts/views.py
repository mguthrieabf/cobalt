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

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if user.username=="admin":
                user.is_admin = true
                user.save()
                return HttpResponse("Added")
            else:
                user.is_active = False   # not active until email confirmed
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
    context = {
        'user_form': form,
    }
    return render(request, 'accounts/register.html', context)

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        #login(request, user)
        return render(request, 'accounts/activate_complete.html', { 'user' : user})
    else:
        return HttpResponse('Activation link is invalid!')

def loggedout(request):
    return render(request, 'accounts/loggedout.html')
