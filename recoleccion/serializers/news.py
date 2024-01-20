from rest_framework import serializers


class GeneralNewsRequestSerializer(serializers.Serializer):
    max_news = serializers.IntegerField(required=False, default=10)


class NewsSerializer(serializers.Serializer):
    title = serializers.CharField()
    link = serializers.CharField()
    video_url = serializers.CharField()
    # content = serializers.CharField()
    image_url = serializers.CharField()
    date = serializers.CharField(source="pubDate")
    description = serializers.CharField()
    source_id = serializers.CharField()  # nos sirve para saber qué fuentes filtrar


class GeneralNewsResponseSerializer(serializers.ListSerializer):
    child = NewsSerializer()


class LegislatorNewsSerializer(serializers.Serializer):
    title = serializers.CharField()
    link = serializers.CharField()
    description = serializers.CharField(source="snippet")
    date = serializers.CharField()
    image_url = serializers.CharField(source="imageUrl")
    source = serializers.CharField()


class LegislatorNewsResponseSerializer(serializers.ListSerializer):
    child = LegislatorNewsSerializer()
