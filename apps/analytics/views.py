from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import MonthlySummarySerializer
from .services.aggregates import TimeSeriesAggregate


class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='monthly-summary')
    def monthly_summary(self, request):
        year = int(request.query_params.get('year'))
        month = int(request.query_params.get('month'))
        data = TimeSeriesAggregate.monthly_series(request.user, year, month)
        serializer = MonthlySummarySerializer(data=data)
        return Response(serializer.data)
