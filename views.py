from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from .excel_generator import generate_excel_report
from datetime import datetime

def summary_table(request):
    return render(request, 'summary-table.html')

def get_execution_log_data(request):
    try:
        with open('execution_log.csv', 'r') as f:
            csv_content = f.read()
        return HttpResponse(csv_content, content_type='text/csv')
    except Exception as e:
        print(f"Error reading execution log: {e}")
        return HttpResponse("", content_type='text/csv')

@require_http_methods(["GET"])
def download_report(request):
    try:
        excel_content = generate_excel_report()
        response = HttpResponse(
            excel_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=Facebook_Report_{datetime.now().strftime("%Y%m%d")}.xlsx'
        return response
    except Exception as e:
        print(f"Error generating report: {e}")
        return HttpResponse(status=500) 