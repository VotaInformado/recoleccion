
# Django REST Framework
from rest_framework.routers import SimpleRouter


from django.contrib import admin
from django.urls import include, path

from informacion.views import PersonViewSet

router = SimpleRouter()

router.register(r'persons', PersonViewSet, basename='persons')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls))
]
