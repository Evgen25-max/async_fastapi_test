from django.conf import settings
from debug_toolbar.toolbar import debug_toolbar_urls
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('movies.api.urls')),
] + debug_toolbar_urls()


if settings.DEBUG:
    urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
