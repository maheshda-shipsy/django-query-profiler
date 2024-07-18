from django_query_profiler.chrome_plugin_helpers.redis_utils import get_host, REDIS_INSTANCE

import json, os, pickle
from collections import defaultdict
from django.template.loader import render_to_string
from django_query_profiler.templates import *


def get_nplus1_data(request, limit=0):
    host = get_host()
    query_profiler_data_list = REDIS_INSTANCE.hvals(host)
    if limit:
        query_profiler_data_list = query_profiler_data_list[:limit]
    final_data = get_formatted_data(query_profiler_data_list)
    detailed_report = render_to_string('django_query_profiler_stack_traces.html', final_data)
    return detailed_report

def get_formatted_data(profiled_data):
    final_dict = {
        'summary' : defaultdict(int),
        'query_signature_to_statistics' : {}
    }
    profiled_data = filter_n1_queries(profiled_data)
    for query_profiled_data in profiled_data:
        summary = query_profiled_data['custom_summary']
        for key, value in summary.items():
            final_dict['summary'][key] += value
        final_dict['query_signature_to_statistics'].update(query_profiled_data['query_signature_to_query_signature_statistics'])
    return final_dict

def filter_n1_queries(profiled_data):
    final_data, unique_keys = [], set()
    for profiled_data in profiled_data:
        query_profiled_data = pickle.loads(profiled_data)
        temp_query_profiled_data = {
            'summary' : query_profiled_data.summary.__dict__,
            'custom_summary' : defaultdict(int),
            'query_signature_to_query_signature_statistics' : {}
        }
        for query_signature, query_statistics in query_profiled_data.query_signature_to_query_signature_statistics.items():
            if query_statistics.frequency > 1:
                stack_trace = query_signature.app_stack_trace[0]
                file_name = f'stockone-wms/wms/{stack_trace.module_name.replace(".", "/")}.py'
                line_no = stack_trace.line_number
                func_name = stack_trace.function_name
                unique_key = (file_name, func_name, line_no)
                if unique_key in unique_keys:
                    continue
                unique_keys.add(unique_key)
                temp_query_profiled_data['custom_summary']['potential_n_plus1_query_count'] += 1
                temp_query_profiled_data['custom_summary']['total_query_execution_time_in_micros'] += query_statistics.query_execution_time_in_micros
                temp_query_profiled_data['custom_summary']['total_db_row_count'] += abs(query_statistics.db_row_count)
                temp_query_profiled_data['custom_summary']['total_query_count'] += query_statistics.frequency
                temp_query_profiled_data['query_signature_to_query_signature_statistics'][query_signature] = query_statistics.__dict__
                temp_query_profiled_data['query_signature_to_query_signature_statistics'][query_signature]['db_row_count'] = abs(query_statistics.db_row_count)
        if temp_query_profiled_data['query_signature_to_query_signature_statistics']:
            final_data.append(temp_query_profiled_data)
    return final_data
