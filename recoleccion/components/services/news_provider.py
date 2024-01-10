import re
import requests
from django.conf import settings
import logging

# Project
from recoleccion.exceptions.custom import NewsProviderLimitReached
from recoleccion.models import StoredNews

logger = logging.getLogger(__name__)


class NewsProvider:
    EXCLUDED_SOURCES = ["elsol"]
    DEFAULT_PAGE_SIZE = 10  # Plan free, no se puede cambiar
    URL = "https://newsdata.io/api/1/news"
    params = {
        "country": "ar",
        "category": "politics",
        "apikey": settings.NEWS_PROVIDER_API_KEY,
    }

    @classmethod
    def _store_news(cls, fetched_news: list):
        logger.info("Storing news...")
        StoredNews.objects.all().delete()  # we only store the latest news
        stored_news = []
        for piece_of_news in fetched_news:
            stored_news_fields = [field.name for field in StoredNews._meta.get_fields()]
            news_info = {field: piece_of_news[field] for field in stored_news_fields if field in piece_of_news}
            news_info["description"] = cls._clean_description(news_info.get("description"))
            stored_piece = StoredNews.objects.create(**news_info)
            stored_news.append(stored_piece)
        return stored_news

    @classmethod
    def _get_stored_news(cls):
        return StoredNews.objects.all().values()

    @classmethod
    def _get_latest_news(cls, total_news):
        news_list = []
        request_params = cls.params.copy()
        while True:
            response = requests.get(cls.URL, params=request_params)
            if response.status_code != 200:
                if response.status_code == 429:
                    raise NewsProviderLimitReached()
                raise Exception("Error getting news")
            response_content = response.json()
            news = response_content["results"]
            for piece_of_news in news:
                source = piece_of_news["source_id"]
                if source in cls.EXCLUDED_SOURCES:
                    continue
                news_list.append(piece_of_news)
                if len(news_list) == total_news:
                    return news_list
            next_page = response_content["nextPage"]
            request_params.update({"page": next_page})

    @classmethod
    def get_latest_news(cls, total_news):
        try:
            fetched_news = cls._get_latest_news(total_news)
            stored_news = cls._store_news(fetched_news)
            return stored_news
        except NewsProviderLimitReached as e:
            logger.warning(e)
            logger.info("Getting stored news...")
            return cls._get_stored_news()

    @classmethod
    def _clean_description(cls, raw_description: str):
        if not raw_description:
            return None

        fixed_description = re.sub(r"\(function\(i,s,o,g,r,a,m\).*\)", "", raw_description)
        fixed_description = fixed_description[:-1]
        fixed_description = fixed_description.strip()
        fixed_description += "."
        return fixed_description
