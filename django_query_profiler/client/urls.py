from django.urls import path

from django_query_profiler.chrome_plugin_helpers import views

GET_QUERY_PROFILED_DATA_NAME = 'get_query_profiled_data'
urlpatterns = [
    path('<str:redis_key>/<str:query_profiler_level>', views.get_query_profiled_data,
         name=GET_QUERY_PROFILED_DATA_NAME),
    path('json_data/<str:redis_key>/<str:query_profiler_level>', views.get_n_plus1_query_data,
         name=GET_QUERY_PROFILED_DATA_NAME),
    path('query_performance/', views.query_performance_details, name='query_performance_details'),
]
