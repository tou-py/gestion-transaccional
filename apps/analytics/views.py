from datetime import date

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import (
    DailyBalanceSerializer,
    MonthlySummarySerializer, WeeklySummarySerializer
)
from .services.aggregates import TimeSeriesAggregate


class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='daily-series')
    def daily_series(self, request):
        try:
            start = request.query_params.get('start')
            end = request.query_params.get('end')
        except KeyError:
            return Response(
                {
                    'detail': 'Parámetros `start` son `end` obligatorios.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        data = TimeSeriesAggregate.daily_series(request.user, date.fromisoformat(start), date.fromisoformat(end))
        serializer = DailyBalanceSerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='weekly-summary')
    def weekly_summary(self, request):
        try:
            start = date.fromisoformat(request.query_params.get('start'))
            weeks = int(request.query_params.get('weeks'))
        except (ValueError, KeyError):
            return Response(
                {
                    'detail': '`start` (YYYY-MM-DD) y `weeks` (int) son obligatorios.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        data = TimeSeriesAggregate.weekly_series(request.user, start, weeks)
        serializer = WeeklySummarySerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='monthly-summary')
    def monthly_summary(self, request):
        year = int(request.query_params.get('year'))
        month = int(request.query_params.get('month'))
        data = TimeSeriesAggregate.monthly_series(request.user, year, month)
        serializer = MonthlySummarySerializer(data=data)
        return Response(serializer.data)
