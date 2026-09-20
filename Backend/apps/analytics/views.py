from datetime import date

from rest_framework.response import Response
from rest_framework.views import APIView

from services.financial_analysis_service import get_financial_analytics

from .date_ranges import RANGES, resolve_range
from .dashboard import build_dashboard


def _parse_range_params(request):
    range_key = request.query_params.get('range', 'CURRENT_MONTH').upper()
    if range_key not in RANGES:
        raise ValueError(f'Unknown range "{range_key}". Choose one of {", ".join(RANGES)}.')

    start = end = None
    if range_key == 'CUSTOM':
        start_param = request.query_params.get('start')
        end_param = request.query_params.get('end')
        if not (start_param and end_param):
            raise ValueError('A custom range requires both "start" and "end" query parameters (YYYY-MM-DD).')
        try:
            start = date.fromisoformat(start_param)
            end = date.fromisoformat(end_param)
        except ValueError as exc:
            raise ValueError('start and end must be valid dates in YYYY-MM-DD format.') from exc

    return range_key, start, end


class DashboardView(APIView):
    def get(self, request):
        try:
            range_key, start, end = _parse_range_params(request)
            bounds = resolve_range(range_key, start=start, end=end)
        except ValueError as exc:
            return Response({'success': False, 'message': str(exc), 'errors': {}}, status=400)

        result = build_dashboard(request.user, bounds['start'], bounds['end'])
        return Response({'success': True, 'range': {'start': bounds['start'], 'end': bounds['end']}, **result})


class AnalyticsView(APIView):
    def get(self, request):
        try:
            range_key, start, end = _parse_range_params(request)
        except ValueError as exc:
            return Response({'success': False, 'message': str(exc), 'errors': {}}, status=400)

        result = get_financial_analytics(request.user, range_key, start=start, end=end)
        return Response({'success': True, **result})
