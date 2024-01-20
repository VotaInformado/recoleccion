import logging

# Project
from recoleccion.components.services.news.news_source import GlobalNewsSource, LegislatorNewsSource
from recoleccion.exceptions.custom import NewsProviderLimitReached
from recoleccion.models import Person, StoredNews


logger = logging.getLogger(__name__)


class NewsProvider:
    @classmethod
    def _store_news(cls, fetched_news: list):
        logger.info("Storing news...")
        StoredNews.objects.all().delete()  # we only store the latest news
        stored_news = []
        for piece_of_news in fetched_news:
            stored_news_fields = [field.name for field in StoredNews._meta.get_fields()]
            news_info = {field: piece_of_news[field] for field in stored_news_fields if field in piece_of_news}
            news_info["description"] = GlobalNewsSource._clean_description(news_info.get("description"))
            stored_piece = StoredNews.objects.create(**news_info)
            stored_news.append(stored_piece)
        return stored_news

    @classmethod
    def _get_stored_news(cls):
        return StoredNews.objects.all().values()

    @classmethod
    def get_global_news(cls, total_news):
        try:
            fetched_news = GlobalNewsSource.get_latest_news(total_news)
            stored_news = cls._store_news(fetched_news)
            return stored_news
        except NewsProviderLimitReached as e:
            logger.warning(e)
            logger.info("Getting stored news...")
            return cls._get_stored_news()

    @classmethod
    def get_legislator_news(cls, legislator: Person):
        legislator_name = legislator.news_search_terms or legislator.full_name
        news = LegislatorNewsSource.fetch_legislator_news(legislator_name)
        return news
