"""
Recolector opcional de tendencias desde Twitter/X.
Usa ntscraper (sin API oficial). Graceful fallback si no está instalado.
Instalar con: pip install ntscraper
"""
import logging
import os
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

SETTINGS_PATH = Path(__file__).parent.parent.parent / "config" / "settings.yaml"

try:
    from ntscraper import Nitter
    _NTSCRAPER_DISPONIBLE = True
except ImportError:
    _NTSCRAPER_DISPONIBLE = False


class TwitterCollector:
    """
    Recolecta tweets y tendencias de Twitter/X.
    Requiere ntscraper instalado: pip install ntscraper
    """

    def __init__(self):
        if not _NTSCRAPER_DISPONIBLE:
            logger.info("ntscraper no disponible — el recolector de Twitter está deshabilitado.")

    def _esta_disponible(self) -> bool:
        return _NTSCRAPER_DISPONIBLE

    def _cargar_keywords(self) -> list[str]:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        return cfg.get("keywords_politica", [])

    def collect_tweets(self, keyword: str, max_results: int = 20) -> list[dict]:
        """Busca tweets recientes sobre una keyword política peruana."""
        if not self._esta_disponible():
            return []
        try:
            scraper = Nitter(log_level=1)
            tweets = scraper.get_tweets(keyword, mode="term", number=max_results)
            resultados = []
            for tweet in tweets.get("tweets", []):
                resultados.append({
                    "texto": tweet.get("text", ""),
                    "usuario": tweet.get("user", {}).get("username", ""),
                    "likes": tweet.get("stats", {}).get("likes", 0),
                    "retweets": tweet.get("stats", {}).get("retweets", 0),
                    "fecha": tweet.get("date", ""),
                    "keyword": keyword,
                    "source": "twitter",
                })
            logger.info("Twitter: %d tweets para '%s'", len(resultados), keyword)
            return resultados
        except Exception as exc:
            logger.warning("Error al recolectar Twitter para '%s': %s", keyword, exc)
            return []

    def collect_all(self) -> list[dict]:
        """Recolecta tweets para todas las keywords configuradas."""
        if not self._esta_disponible():
            return []
        keywords = self._cargar_keywords()
        todos = []
        for kw in keywords[:5]:  # limitar a 5 para no abusar
            todos.extend(self.collect_tweets(kw))
        return todos
