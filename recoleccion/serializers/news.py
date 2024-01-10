from rest_framework import serializers


class NewsRequestSerializer(serializers.Serializer):
    max_news = serializers.IntegerField(required=False, default=10)


class NewsSerializer(serializers.Serializer):
    title = serializers.CharField()
    link = serializers.CharField()
    video_url = serializers.CharField()
    # content = serializers.CharField()
    image_url = serializers.CharField()
    pubDate = serializers.CharField()
    description = serializers.CharField()
    source_id = serializers.CharField()  # nos sirve para saber qué fuentes filtrar


class NewsResponseSerializer(serializers.ListSerializer):
    child = NewsSerializer()
