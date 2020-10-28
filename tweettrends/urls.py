from django.conf.urls import patterns, include, url
from django.contrib import admin
from tweettrendsapp.views import database_info
from tweettrendsapp.views import index
from tweettrendsapp.views import about
from tweettrendsapp.views import sentiment_top_trends
from tweettrendsapp.views import sentiment_query

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings

urlpatterns = [
    # Examples:
    # url(r'^$', 'tweettrends.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^db', database_info, name='db'),
    url(r'^$', index, name='index'),
    url(r'^about$', about, name='about'),
    url(r'^sentiment_top_trends$', sentiment_top_trends, name='sentiment_top_trends'),
    url(r'^sentiment_query$', sentiment_query, name='sentiment_query'),
]


urlpatterns += staticfiles_urlpatterns()

if not settings.DEBUG:
    urlpatterns += patterns('',
                            (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
                            )

