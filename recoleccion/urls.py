# Django
from rest_framework.routers import SimpleRouter
from django.http import HttpResponse
from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect

# Views
from recoleccion.views import PersonViewSet
from recoleccion.views.deputies import DeputiesViewSet
from recoleccion.views.senate import SenateViewSet

router = SimpleRouter()

router.register(r"persons", PersonViewSet, basename="persons")
router.register(r"deputies", DeputiesViewSet, basename="deputy_seats")
router.register(r"senators", SenateViewSet, basename="senators")


def redirect_to_health(request):
    return redirect('/health/')

def health_check(request):
    return HttpResponse("OK")


urlpatterns = [
    path("", redirect_to_health),
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health_check"),
    path("", include(router.urls)),
]
