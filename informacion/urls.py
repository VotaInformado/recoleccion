# Django
from rest_framework.routers import SimpleRouter
from django.http import HttpResponse
from django.contrib import admin
from django.urls import include, path

# Views
from informacion.views import PersonViewSet

router = SimpleRouter()

router.register(r"persons", PersonViewSet, basename="persons")


def health_check(request):
    return HttpResponse("OK")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", health_check, name="health_check"),
    path("health/", health_check, name="health_check"),
    path("info/", include(router.urls)),
]
