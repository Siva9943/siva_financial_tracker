from datetime import date

from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from services.report_export import EXPORTERS
from services.report_service import (
    ReportError,
    build_budget_report,
    build_dividend_report,
    build_expense_report,
    build_investment_report,
    build_investment_transaction_report,
    build_loan_report,
    build_monthly_report,
    build_portfolio_performance_report,
    build_repayment_report,
    build_yearly_report,
)

REPORT_TYPES = (
    'monthly', 'yearly', 'loan', 'expense', 'budget', 'repayment',
    'investment', 'portfolio_performance', 'dividend', 'investment_transaction',
)


def _int_param(request, name):
    value = request.query_params.get(name)
    return int(value) if value else None


def _date_param(request, name):
    value = request.query_params.get(name)
    return date.fromisoformat(value) if value else None


class ReportView(APIView):
    def get(self, request, report_type):
        if report_type not in REPORT_TYPES:
            return Response(
                {'success': False, 'message': f'Unknown report type "{report_type}".', 'errors': {}}, status=400
            )

        try:
            report = self._build_report(request, report_type)
        except (ReportError, ValueError) as exc:
            return Response({'success': False, 'message': str(exc), 'errors': {}}, status=400)

        # Named "export", not "format" — DRF reserves the "format" query param for its own
        # content-negotiation (URL_FORMAT_OVERRIDE) and 404s on any value it doesn't
        # recognize as a registered renderer, before this view method ever runs.
        export_format = request.query_params.get('export', 'json')
        if export_format == 'json':
            return Response({'success': True, 'report': report})

        if export_format not in EXPORTERS:
            return Response(
                {'success': False, 'message': f'Unknown export format "{export_format}". Choose json, csv, xlsx, or pdf.', 'errors': {}},
                status=400,
            )

        exporter, content_type, extension = EXPORTERS[export_format]
        content = exporter(report)
        filename = f'{report_type}-report-{date.today().isoformat()}.{extension}'

        response = HttpResponse(content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    def _build_report(self, request, report_type):
        user = request.user
        month = _int_param(request, 'month')
        year = _int_param(request, 'year')

        if report_type == 'monthly':
            return build_monthly_report(user, month=month, year=year)
        if report_type == 'yearly':
            return build_yearly_report(user, year=year)
        if report_type == 'loan':
            return build_loan_report(user)
        if report_type == 'budget':
            return build_budget_report(user, month=month, year=year)
        if report_type == 'repayment':
            return build_repayment_report(user, plan_id=_int_param(request, 'plan_id'))
        if report_type == 'investment':
            return build_investment_report(user)
        if report_type == 'portfolio_performance':
            return build_portfolio_performance_report(user)
        if report_type == 'dividend':
            return build_dividend_report(user, start=_date_param(request, 'start'), end=_date_param(request, 'end'))

        # expense / investment_transaction — default to the current month if no explicit range is given
        start = _date_param(request, 'start')
        end = _date_param(request, 'end')
        if not (start and end):
            today = date.today()
            start, end = today.replace(day=1), today
        if end < start:
            raise ValueError('end must not be before start.')
        if report_type == 'investment_transaction':
            return build_investment_transaction_report(user, start=start, end=end)
        return build_expense_report(user, start=start, end=end)
