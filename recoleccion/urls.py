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
from recoleccion.views.legislators import (
    LegislatorsViewSet,
    LegislatorVotesViewSet,
    NeuralNetworkLegislatorViewSet,
    LegislatorLawProjectsViewSet,
)
from recoleccion.views.prediction import PredictionViewSet
from recoleccion.views.senate import SenateViewSet
from recoleccion.views.laws import LawsViewSet
from recoleccion.views.law_projects import (
    LawProjectsViewSet,
    LawProjectVotesViewSet,
    NeuralNetworkProjectsViewSet,
)
from recoleccion.views.parties import (
    PartiesViewSet,
    PartiesAuthorsProjectsCountViewSet,
    PartiesLawProjectsViewSet,
    PartiesLegislatorsViewSet,
    PartiesLawProjectVotesViewSet,
)
from recoleccion.views.votes import NeuralNetworkVotesViewSet
from recoleccion.views.authors import NeuralNetworkAuthorsViewSet

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

# Front end endpoints

router = SimpleRouter()

router.register(r"legislators", LegislatorsViewSet, basename="legislators")
router.register(r"persons", PersonViewSet, basename="persons")
router.register(r"deputies", DeputiesViewSet, basename="deputy_seats")
router.register(r"senators", SenateViewSet, basename="senators")
router.register(r"laws", LawsViewSet, basename="laws")
router.register(r"law-projects", LawProjectsViewSet, basename="law-project")
router.register(
    r"law-projects/(?P<law_project_id>[^/.]+)/votings",
    LawProjectVotesViewSet,
    basename="law-project-votings",
)
router.register(
    r"legislators/(?P<legislator_id>[^/.]+)/votes",
    LegislatorVotesViewSet,
    basename="legislator-votes",
)
router.register(
    r"legislators/(?P<legislator_id>[^/.]+)/law-projects",
    LegislatorLawProjectsViewSet,
    basename="legislator-law-projects",
)
router.register(r"parties", PartiesViewSet, basename="parties")
router.register(
    r"parties/(?P<party_id>[^/.]+)/authorships",
    PartiesAuthorsProjectsCountViewSet,
    basename="party-authorships",
)
router.register(
    r"parties/(?P<party_id>[^/.]+)/law-projects",
    PartiesLawProjectsViewSet,
    basename="party-law-projects",
)
router.register(
    r"parties/(?P<party_id>[^/.]+)/legislators",
    PartiesLegislatorsViewSet,
    basename="party-legislators",
)
router.register(
    r"parties/(?P<party_id>[^/.]+)/votes",
    PartiesLawProjectVotesViewSet,
    basename="party-legislators",
)

# Neural network data endpoints

network_router = SimpleRouter()

network_router.register(r"votes", NeuralNetworkVotesViewSet, basename="votes")
network_router.register(r"authors", NeuralNetworkAuthorsViewSet, basename="authors")
network_router.register(
    r"law-projects", NeuralNetworkProjectsViewSet, basename="law-projects"
)
network_router.register(
    r"legislators", NeuralNetworkLegislatorViewSet, basename="legislators"
)
network_router.register(r"parties", PartiesViewSet, basename="parties")
network_router.register(r"", PredictionViewSet, basename="predictions")


def redirect_to_health(request):
    return redirect("/health/")


def health_check(request):
    return HttpResponse("OK")


urlpatterns = [
    path("", redirect_to_health),
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health_check"),
    path("", include(router.urls)),
    path("neural-network/", include(network_router.urls)),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "swagger.json", schema_view.without_ui(cache_timeout=0), name="schema-json"
    ),  # To download the swagger.json
]
