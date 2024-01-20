import re
import requests
from django.conf import settings
import logging
import json

# Project
from recoleccion.exceptions.custom import NewsProviderLimitReached

logger = logging.getLogger(__name__)

DEFAULT_LEGISLATOR_NEWS = [
    {
        "title": "Para Javier Milei, lo peor no pasó: cuáles serán los meses más complicados según el Presidente",
        "link": "https://www.clarin.com/opinion/javier-milei-peor-paso-meses-complicados-presidente_0_ruLPNniu1r.html",
        "snippet": "Mientras algunos economistas admirados por Javier Milei, como el ex ministro Domingo Cavallo, se atreven a pronosticar una fuerte baja de la...",
        "date": "hace 7 horas",
        "source": "Clarin.com",
        "imageUrl": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRSKMAttc3vVzlr73zYcHqnHIVXQflENvmacqqzz4bDtrGIgVMFuVTL9iE8LA&s",
        "position": 1,
    },
    {
        "title": 'Reapareció Luis Barrionuevo y le dejó un duro mensaje a Milei: "Va a tener que.."',
        "link": "https://www.cronista.com/economia-politica/barrionuevo-reaparecio-critico-las-primeras-medidas-de-milei-y-aconsejo-a-bullrich-sobre-el-paro-general/",
        "snippet": "El dirigente gastronómico, que había apoyado a Milei durante las elecciones, criticó las primeras medidas duras del Gobierno y a los que...",
        "date": "hace 1 día",
        "source": "El Cronista",
        "imageUrl": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTNU-V6Pgv1ylIRt_WDKPT7iaICldnZFAixMbJ39_APxFeQwa2XYhiOpJF6DQ&s",
        "position": 2,
    },
    {
        "title": "Javier Milei: “El 60% del ajuste cae sobre el sector público”",
        "link": "https://chequeado.com/ultimas-noticias/javier-milei-el-60-del-ajuste-cae-sobre-el-sector-publico/",
        "snippet": "El presidente de la Nación, Javier Milei, aseguró, en declaraciones al programa La Noche de Mirtha, que se emite por Canal 13, que “el 60%...",
        "date": "hace 1 día",
        "source": "Chequeado",
        "imageUrl": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRoxP8-K4Xr8RzVSzBf7LpPAClITIx8ZvmgJwmQznvTyIQA1c1Evvh0tdHFvA&s",
        "position": 3,
    },
]


class GlobalNewsSource:
    EXCLUDED_SOURCES = ["elsol"]
    DEFAULT_PAGE_SIZE = 10  # Plan free, no se puede cambiar
    URL = "https://newsdata.io/api/1/news"
    params = {
        "country": "ar",
        "category": "politics",
        "apikey": settings.GLOBAL_NEWS_PROVIDER_API_KEY,
    }

    @classmethod
    def get_latest_news(cls, total_news):
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
    def _clean_description(cls, raw_description: str):
        if not raw_description:
            return None

        fixed_description = re.sub(r"\(function\(i,s,o,g,r,a,m\).*\)", "", raw_description)
        fixed_description = fixed_description[:-1]
        fixed_description = fixed_description.strip()
        fixed_description += "."
        return fixed_description


class LegislatorNewsSource:
    URL = "https://google.serper.dev/news"

    @classmethod
    def fetch_legislator_news(cls, legislator_name: str):
        if not settings.LEGISLATOR_NEWS_ENABLED:
            return DEFAULT_LEGISLATOR_NEWS
        payload = json.dumps({"q": legislator_name, "gl": "ar", "hl": "es"})
        headers = {"X-API-KEY": settings.LEGISLATOR_NEWS_PROVIDER_API_KEY, "Content-Type": "application/json"}
        logger.info(f"Searching news for legislator {legislator_name}")
        response = requests.request("POST", cls.URL, headers=headers, data=payload)
        news = response.json()["news"]  # 10 by default, we don't "pay" less for less than 10
        return news
