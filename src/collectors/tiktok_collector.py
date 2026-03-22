"""
Recolector opcional de tendencias desde TikTok.
Usa TikTokApi (sin API oficial). Graceful fallback si no está instalado.
Instalar con: pip install TikTokApi && playwright install chromium
"""
import asyncio
import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

SETTINGS_PATH = Path(__file__).parent.parent.parent / "config" / "settings.yaml"

try:
    from TikTokApi import TikTokApi
    _TIKTOKAPI_DISPONIBLE = True
except ImportError:
    _TIKTOKAPI_DISPONIBLE = False


class TikTokCollector:
    """
    Recolecta videos y hashtags de tendencia en TikTok.
    Requiere TikTokApi y playwright: pip install TikTokApi && playwright install chromium
    """

    def __init__(self):
        if not _TIKTOKAPI_DISPONIBLE:
            logger.info("TikTokApi no disponible — el recolector de TikTok está deshabilitado.")

    def _esta_disponible(self) -> bool:
        return _TIKTOKAPI_DISPONIBLE

    def _cargar_keywords(self) -> list[str]:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        return cfg.get("keywords_politica", [])

    async def _fetch_hashtag(self, api: "TikTokApi", hashtag: str, count: int = 10) -> list[dict]:
        """Busca videos por hashtag en TikTok."""
        resultados = []
        try:
            tag = api.hashtag(name=hashtag)
            async for video in tag.videos(count=count):
                resultados.append({
                    "id": video.id,
                    "descripcion": video.as_dict.get("desc", ""),
                    "likes": video.as_dict.get("stats", {}).get("diggCount", 0),
                    "compartidos": video.as_dict.get("stats", {}).get("shareCount", 0),
                    "vistas": video.as_dict.get("stats", {}).get("playCount", 0),
                    "hashtag": hashtag,
                    "source": "tiktok",
                })
        except Exception as exc:
            logger.warning("Error en TikTok para hashtag '%s': %s", hashtag, exc)
        return resultados

    async def collect_all_async(self) -> list[dict]:
        """Recolecta videos de TikTok para keywords políticas peruanas."""
        if not self._esta_disponible():
            return []
        keywords = self._cargar_keywords()
        # Convertir keywords a hashtags (sin espacios)
        hashtags = [kw.replace(" ", "").lower() for kw in keywords[:5]]
        todos = []
        async with TikTokApi() as api:
            await api.create_sessions(num_sessions=1, sleep_after=3)
            for ht in hashtags:
                todos.extend(await self._fetch_hashtag(api, ht))
        return todos

    def collect_all(self) -> list[dict]:
        """Wrapper sincrónico de collect_all_async."""
        if not self._esta_disponible():
            return []
        return asyncio.run(self.collect_all_async())
