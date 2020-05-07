from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import login
from .models import User
from .forms import UserRegisterForm
from .tokens import account_activation_token
from cobalt.settings import DEFAULT_FROM_EMAIL
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import UserUpdateForm, BlurbUpdateForm, AutoTopUpUpdateForm
import ipinfo
from logs.views import get_client_ip, log_event
from django.conf import settings
from organisations.models import MemberOrganisation
import cobalt.settings
from payments.models import AutoTopUpConfig

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False   # not active until email confirmed
            user.system_number = user.username
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activate your account.'
            message = render_to_string('accounts/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'org': settings.GLOBAL_ORG,
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
        return HttpResponse('Activation link is invalid or already used!')

def loggedout(request):
    return render(request, 'accounts/loggedout.html')

@login_required()
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!', extra_tags='cobalt-message-success')
            log_event(request = request,
                      user = request.user.full_name,
                      severity = "INFO",
                      source = "Accounts",
                      sub_source = "change_password",
                      message = "Password change successful")
            return render(request, 'accounts/change_password.html', {
                    'form': form
                })
        else:
            log_event(request = request,
                      user = request.user.full_name,
                      severity = "WARN",
                      source = "Accounts",
                      sub_source = "change_password",
                      message = "Password change failed")
            messages.error(request, 'Please correct the error below.', extra_tags='cobalt-message-error')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {
        'form': form
    })

@login_required()
def member_detail_ajax(request):
        if request.method == "GET":
            if 'member_id' in request.GET:
                member_id = request.GET.get("member_id")
                member = get_object_or_404(User, pk=member_id)
                clubs = MemberOrganisation.objects.filter(member = member)
                if request.is_ajax:
                    global_org = settings.GLOBAL_ORG
                    html = render_to_string(
                        template_name="accounts/member_ajax.html",
                        context={"member": member, 'clubs': clubs, 'global_org': global_org}
                    )
                    data_dict = {"data": html}
                    return JsonResponse(data=data_dict, safe=False)

@login_required()
def search_ajax(request):

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
        print(members)

        if request.is_ajax:
            print("ok")
            if members.count()>30:
                msg="Too many results (%s)" % members.count()
                members=None
            html = render_to_string(
                template_name="accounts/search_results.html",
                context={"members": members, "msg": msg}
            )

            data_dict = {"data": html}

            return JsonResponse(data=data_dict, safe=False)

    return render(request, "accounts/search_results.html", context={'members': members, 'msg': msg})

@login_required
def profile(request):
    msg=""
    if request.method == 'POST':
        form = UserUpdateForm(data=request.POST, instance=request.user)
        top = AutoTopUpConfig.objects.filter(member=request.user).last()
        topupform = AutoTopUpUpdateForm(data=request.POST, instance=top)
        if form.is_valid() and topupform.is_valid():
            msg="Profile Updated"
            form.save()
            print(topupform)
            topupform.save()
            print(msg)
        else:
            print("invlaid")
            print(form.errors)
            print(topupform.errors)
    else:
# Fix DOB format for browser - expects DD/MM/YYYY
        if request.user.dob:
            request.user.dob=request.user.dob.strftime("%d/%m/%Y")

        form = UserUpdateForm(instance=request.user)
        top = AutoTopUpConfig.objects.filter(member=request.user).last()
        topupform = AutoTopUpUpdateForm(instance=top)
    blurbform = BlurbUpdateForm(instance=request.user)

    access_token='70691e3380c3b2'
    handler = ipinfo.getHandler(access_token)
    ip_address = get_client_ip(request)
    ip_details = handler.getDetails(ip_address)

    context = {
        'form': form,
        'blurbform': blurbform,
        'topupform': topupform,
        'msg': msg,
        'ip_details': ip_details,
    }
    return render(request, 'accounts/profile.html', context)

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
    return render(request, 'accounts/profile.html', context)


@login_required
def public_profile(request, pk):
    profile = get_object_or_404(User, pk=pk)
    return render(request, 'accounts/public_profile.html', {'profile': profile})
