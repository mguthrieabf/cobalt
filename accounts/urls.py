from django.urls import path
from django.http import HttpResponse
from django.contrib.auth.views import PasswordResetView
from . import views

app_name = "accounts"

urlpatterns = [
    path("register", views.register, name="register"),
    path("loggedout", views.loggedout, name="loggedout"),
    path("signin", views.loggedout, name="signin"),
    path("search-ajax", views.search_ajax, name="member_search_M2M_ajax"),
    path("detail-ajax", views.member_detail_M2M_ajax, name="member_detail_M2M_ajax"),
    path("member-search-ajax", views.member_search_ajax, name="member_search_ajax"),
    path("member-details-ajax", views.member_details_ajax, name="member_details_ajax"),
    path("change-password", views.change_password, name="change_password"),
    path("activate/<str:uidb64>/<str:token>/", views.activate, name="activate"),
    path("profile", views.profile, name="user_profile"),
    path("update-blurb", views.blurb_form_upload, name="user_blurb"),
    #    path("guthrie-password", views.guthrie_password, name="guthrie1"),
    #    path("password_reset/", views.guthrie_password, name="guthrie"),
    path("public-profile/<int:pk>/", views.public_profile, name="public_profile"),
    # path(
    #     "accounts/password_reset/",
    #     PasswordResetView.as_view(extra_email_context={"html_email_template_name": "registration/html_password_reset_email.html"}),
    #     name="password_reset",
    # ),
    #    path('accounts/password_reset/', PasswordResetView.as_view(extra_context={'html_email_template_name':'registration/html_password_reset_email.html'})),
    #    path('password/reset/', password_reset, {'html_email_template_name':'registration/html_password_reset_email.html', name='password_reset'),
    #    path('accounts/logout/', auth_views.LogoutView.as_view(
    # extra_context={'foo':'bar'}
    path(
        "password_reset/html_email_template/",
        PasswordResetView.as_view(
            html_email_template_name="registration/html_password_reset_email2.html"
        ),
    ),
]


def not_found_handler(request, exception=None):
    return HttpResponse("Error handler content", status=403)


handler404 = not_found_handler
