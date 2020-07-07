from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from .models import Organisation


@login_required()
def org_search_ajax(request):
    """ Ajax org search function. Used by the generic org search.

    Args:
        orgname - partial org name to search for.

    Returns:
        HttpResponse - either a message or a list of users in HTML format.
    """

    msg = ""

    if request.method == "GET":

        if "orgname" not in request.GET:
            return HttpResponse("orgname missing from request")
        else:
            search_org_name = request.GET.get("orgname")
            orgs = Organisation.objects.filter(name__icontains=search_org_name)

        if request.is_ajax:
            if orgs.count() > 30:
                msg = "Too many results (%s)" % orgs.count()
                orgs = None
            elif orgs.count() == 0:
                msg = "No matches found"
            html = render_to_string(
                template_name="organisations/org_search_ajax.html",
                context={"orgs": orgs, "msg": msg},
            )

            data_dict = {"data": html}

            return JsonResponse(data=data_dict, safe=False)

    return HttpResponse("invalid request")


@login_required()
def org_detail_ajax(request):
    """ Returns basic info on an org for the generic org search.

    Ajax call to get basic info on an org. Will return an empty json array
    if the org number is invalid.

    Args:
        org_id - org number

    Returns:
        Json array: address etc.
    """

    if request.method == "GET":
        if "org_id" in request.GET:
            org_id = request.GET.get("org_id")
            org = get_object_or_404(Organisation, pk=org_id)
            if request.is_ajax:
                html = render_to_string(
                    template_name="organisations/org_detail_ajax.html",
                    context={"org": org},
                )
                data_dict = {"data": html, "org": org.name}
                return JsonResponse(data=data_dict, safe=False)
    return JsonResponse(data={"error": "Invalid request"})
