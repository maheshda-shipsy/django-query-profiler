import json
from typing import Dict

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from django_query_profiler.chrome_plugin_helpers import redis_utils
from django_query_profiler.query_profiler_storage import QueryProfiledData, QueryProfilerLevel
from django.contrib.auth.decorators import login_required
from django_query_profiler.chrome_plugin_helpers.utils import get_nplus1_data

QUERY_PROFILER_LEVEL_TO_TEMPLATE: Dict[str, str] = {
    QueryProfilerLevel.QUERY_SIGNATURE.name: 'django_query_profiler_level_query_signature.html',
    QueryProfilerLevel.QUERY.name: 'django_query_profiler_level_query.html',
}


def get_query_profiled_data(request, redis_key: str, query_profiler_level: str) -> HttpResponse:
    host = redis_utils.get_host()
    query_profiled_data: QueryProfiledData = redis_utils.retrieve_data(redis_key, host)
    context = {
        'summary': query_profiled_data.summary,
        'query_signature_to_statistics': query_profiled_data.query_signature_to_query_signature_statistics,
        'flamegraphStack': json.dumps(query_profiled_data.flamegraph_stack),
    }
    return render(request, QUERY_PROFILER_LEVEL_TO_TEMPLATE[query_profiler_level], context)

def get_n_plus1_query_data(request, redis_key: str, query_profiler_level: str) -> JsonResponse:
    host = redis_utils.get_host()
    query_profiled_data: QueryProfiledData = redis_utils.retrieve_data(redis_key, host)
    
    n_plus1_queries = []
    for query_signature, query_statistics in query_profiled_data.query_signature_to_query_signature_statistics.items():
        if query_statistics.frequency > 1:
            stack_trace = query_signature.app_stack_trace[0]
            file_name = f'stockone-wms/wms/{stack_trace.module_name.replace(".", "/")}.py'
            line_no = stack_trace.line_number
            func_name = stack_trace.function_name
            n_plus1_queries.append({
                'query': query_signature.query_without_params,
                'frequency': query_statistics.frequency,
                'query_execution_time_in_micros': query_statistics.query_execution_time_in_micros,
                'db_row_count': query_statistics.db_row_count,
                'file_name' : file_name,
                'func_name' : func_name,
                'line_no' : line_no,
                'recommendation': query_signature.analysis.name if query_signature.analysis.visible_in_ui else None
            })
    
    return JsonResponse({'n_plus1_queries': n_plus1_queries})

@login_required(login_url='/admin/login/')
def query_performance_details(request):
    limit= int(request.GET.get('limit') or  0)
    query_data = get_nplus1_data(request, limit)
    return HttpResponse(query_data)
