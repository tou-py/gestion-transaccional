from rest_framework import serializers


class DailyBalanceSerializer(serializers.Serializer):
    day = serializers.DateField()
    balance = serializers.FloatField()


class MonthlySummarySerializer(serializers.Serializer):
    year = serializers.IntegerField()
    month = serializers.IntegerField()
    balance = serializers.FloatField()
    incomes = serializers.FloatField()
    expenses = serializers.FloatField()
    daily_series = DailyBalanceSerializer(many=True)


class WeeklyBalanceSerializer(serializers.Serializer):
    week_start = serializers.DateField()
    week_end = serializers.DateField()
    balance = serializers.FloatField()


class WeeklySummarySerializer(serializers.Serializer):
    # many=True, así que no campos extra necesarios aquí
    pass
