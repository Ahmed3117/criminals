import django
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView
from django.conf import settings

import debug_toolbar



urlpatterns = [
    path('__debug__/', include(debug_toolbar.urls)),
    path('admin/', admin.site.urls),
    # path('nested_admin/', include('nested_admin.urls')),
    path('favicon.ico/', RedirectView.as_view(url=staticfiles_storage.url('imgs/logo.ico'))),
    path('', include('about.urls',namespace='about')),
]
urlpatterns+=static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns+=static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
