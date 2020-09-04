# pylint: disable=missing-module-docstring,missing-class-docstring
from django.urls import path

# from django.http import HttpResponse
from . import views

app_name = "accounts"  # pylint: disable=invalid-name

urlpatterns = [
    path("register", views.register, name="register"),
    path("loggedout", views.loggedout, name="loggedout"),
    path("signin", views.loggedout, name="signin"),
    path("search-ajax", views.search_ajax, name="member_search_M2M_ajax"),
    path("detail-ajax", views.member_detail_m2m_ajax, name="member_detail_m2m_ajax"),
    path("member-search-ajax", views.member_search_ajax, name="member_search_ajax"),
    path(
        "system-number-search-ajax",
        views.system_number_search_ajax,
        name="system_number_search_ajax",
    ),
    path("member-details-ajax", views.member_details_ajax, name="member_details_ajax"),
    path("change-password", views.change_password, name="change_password"),
    path("activate/<str:uidb64>/<str:token>/", views.activate, name="activate"),
    path("profile", views.profile, name="user_profile"),
    path("settings", views.user_settings, name="user_settings"),
    path("update-blurb", views.blurb_form_upload, name="user_blurb"),
    path("password_reset/", views.html_email_reset, name="html_email_reset"),
    path("public-profile/<int:pk>/", views.public_profile, name="public_profile"),
]

# def not_found_handler(request, exception=None):
#     return HttpResponse("Error handler content", status=403)
#
#
# handler404 = not_found_handler
