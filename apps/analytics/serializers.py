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
