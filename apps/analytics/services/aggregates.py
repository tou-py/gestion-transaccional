from datetime import date, timedelta
from typing import Any, List, Dict

from django.db.models import Sum, F, Case, When, DecimalField, Value, QuerySet
from django.db.models.functions import TruncDay

from apps.accounts.models import User
from apps.transactions.models import Transaction


class TimeSeriesAggregate:
    """
    Clase que provee metodos para obtener series temporales de balances,
    ingresos o gratos por dia, semana o mes
    """

    @staticmethod
    def _base_queryset(user: User, start_date: date, end_date: date) -> QuerySet[Transaction]:
        """
        Filtrado por usuario, rango de fechas y un monto anotado:
        positivo para ingresos y negativo para egresos
        """
        query = Transaction.objects.filter(
            user=user,
            date__date__gte=start_date,
            date__date__lte=end_date,
        ).annotate(
            signed_amount=Case(
                When(category__category_type='INGRESO', then=F('amount')),
                When(category__category_type='EGRESO', then=F('amount') * Value(-1)),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )
        return query

    @staticmethod
    def daily_series(user: User, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        Retorna una lista de balances para cada dia del rango proporcionado
        """
        query = TimeSeriesAggregate._base_queryset(user, start_date, end_date)
        query = query.annotate(period=TruncDay('date'))
        agg = query.values('period').annotate(
            balance=Sum('signed_amount'),
        ).order_by('period')

        # Asegurar que los dias sin transacciones aparezcan con 0
        days = (end_date - start_date).days + 1
        lookup = {
            row['period'].date(): float(row['balance'] or 0) for row in agg
        }
        return [
            {
                'day': start_date + timedelta(days=i), 'balance': lookup.get(start_date + timedelta(day=i), 0.0)
            } for i in range(days)
        ]

    @staticmethod
    def weekly_series(user, start_date: date, weeks: int) -> List[Dict[str, Any]]:
        """
        Genera un resumen semanal de balance:
        - `week_start`: fecha de inicio de la semana (start_date + 7*i días)
        - `week_end`  : fecha de fin de la semana (6 días después)
        - `balance`   : suma de signed_amount en ese rango
        """
        results: List[Dict[str, Any]] = []

        for i in range(weeks):
            week_start = start_date + timedelta(days=i * 7)
            week_end = week_start + timedelta(days=6)

            # Reutilizamos el método genérico para filtrar y anotar signed_amount
            qs = TimeSeriesAggregate._base_queryset(user, week_start, week_end)

            # Agregación de balance en la semana
            total = qs.aggregate(week_balance=Sum('signed_amount'))['week_balance'] or 0

            results.append({
                'week_start': week_start,
                'week_end': week_end,
                'balance': float(total),
            })

        return results

    @staticmethod
    def monthly_series(user, year: int, month: int) -> Dict[str, Any]:
        """
        Balance total, ingresos y gastos del mes, y serie diaria interna.
        """
        # Fecha inicio/fin del mes
        start_date = date(year, month, 1)
        # Para fin de mes usamos un truco:
        next_month = start_date.replace(day=28) + timedelta(days=4)
        end_date = next_month - timedelta(days=next_month.day)

        # Serie diaria (reutiliza daily_series)
        series = TimeSeriesAggregate.daily_series(user, start_date, end_date)

        # Balance agregado del mes
        qs = TimeSeriesAggregate._base_queryset(user, start_date, end_date)
        total = qs.aggregate(balance=Sum('signed_amount'))['balance'] or 0

        # Ingresos y egresos por separado
        ingresos = qs.filter(signed_amount__gte=0).aggregate(Sum('signed_amount'))['signed_amount__sum'] or 0
        egresos = - (qs.filter(signed_amount__lt=0).aggregate(Sum('signed_amount'))['signed_amount__sum'] or 0)

        return {
            'year': year,
            'month': month,
            'balance': float(total),
            'ingresos': float(ingresos),
            'egresos': float(egresos),
            'daily_series': series,
        }
