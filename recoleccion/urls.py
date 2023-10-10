# Django
from rest_framework.routers import SimpleRouter
from django.http import HttpResponse
from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# Views
from recoleccion.views import PersonViewSet
from recoleccion.views.deputies import DeputiesViewSet
from recoleccion.views.legislators import LegislatorsViewSet
from recoleccion.views.senate import SenateViewSet
from recoleccion.views.laws import LawsViewSet
from recoleccion.views.law_projects import LawProjectsViewSet, LawProyectVotesViewSet

schema_view = get_schema_view(
    openapi.Info(
        title="Your API",
        default_version="v1",
        description="Your API description",
        terms_of_service="https://www.yourapp.com/terms/",
        contact=openapi.Contact(email="contact@yourapp.com"),
        license=openapi.License(name="Your License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


router = SimpleRouter()

router.register(r"legislators", LegislatorsViewSet, basename="legislators")
router.register(r"persons", PersonViewSet, basename="persons")
router.register(r"deputies", DeputiesViewSet, basename="deputy_seats")
router.register(r"senators", SenateViewSet, basename="senators")
router.register(r"laws", LawsViewSet, basename="laws")
router.register(r"law-projects", LawProjectsViewSet, basename="law-project")
router.register(
    r"law-projects/(?P<law_project_id>[^/.]+)/votings",
    LawProyectVotesViewSet,
    basename="law-project-votings",
)


def redirect_to_health(request):
    return redirect("/health/")


def health_check(request):
    return HttpResponse("OK")


urlpatterns = [
    path("", redirect_to_health),
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health_check"),
    path("", include(router.urls)),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "swagger.json", schema_view.without_ui(cache_timeout=0), name="schema-json"
    ),  # To download the swagger.json
]
