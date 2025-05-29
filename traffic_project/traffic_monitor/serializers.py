from rest_framework import serializers

class ChartDataSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    data = serializers.ListField(child=serializers.FloatField()) # Changed to FloatField for potentially non-integer data, like averages in future

class CombinedChartDataSerializer(serializers.Serializer):
    distribution_chart = ChartDataSerializer()
    timeline_chart = ChartDataSerializer()
