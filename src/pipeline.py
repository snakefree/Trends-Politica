"""
Módulo de pipeline compartido para recolección de datos.

Centraliza la lógica de recolección usada desde main.py, mcp_server.py y scheduler.py,
evitando triplicar el mismo código en tres puntos de entrada distintos.
"""
import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def recolectar_datos(fuente: str = "all") -> list[dict]:
    """
    Recolecta datos de todas las fuentes configuradas y los retorna como lista unificada.

    Parámetros:
        fuente: 'all', 'rss', 'google_trends', 'twitter' o 'tiktok'

    Retorna una lista de dicts con los datos crudos recolectados.
    Las fuentes opcionales (google_trends, twitter, tiktok) fallan de forma silenciosa
    con log de advertencia si no están disponibles.
    """
    from src.collectors.rss_collector import RSSCollector
    from src.collectors.twitter_collector import TwitterCollector
    from src.collectors.tiktok_collector import TikTokCollector

    datos: list[dict] = []

    if fuente in ("all", "rss"):
        logger.info("Recolectando RSS...")
        rss = RSSCollector()
        datos.extend(await rss.recolectar_todo())

    if fuente in ("all", "google_trends"):
        logger.info("Consultando Google Trends...")
        try:
            from src.collectors.google_trends_collector import GoogleTrendsCollector
            gt = GoogleTrendsCollector()
            datos.extend(await asyncio.to_thread(gt.recolectar_todo))
        except ImportError:
            logger.warning("Google Trends no disponible (pytrends no instalado)")

    if fuente in ("all", "twitter"):
        logger.info("Recolectando Twitter/X...")
        tw = TwitterCollector()
        datos.extend(await asyncio.to_thread(tw.recolectar_todo))

    if fuente in ("all", "tiktok"):
        logger.info("Recolectando TikTok...")
        tt = TikTokCollector()
        datos.extend(await asyncio.to_thread(tt.recolectar_todo))

    logger.info("Total recolectado: %d items (fuente=%s)", len(datos), fuente)
    return datos


def guardar_cache(datos: list[dict], directorio_datos: Path) -> Path:
    """
    Guarda los datos crudos en data/raw_YYYY-MM-DD.json.

    Retorna la ruta del archivo guardado.
    """
    import json
    from datetime import date

    directorio_datos.mkdir(parents=True, exist_ok=True)
    ruta = directorio_datos / f"raw_{date.today().isoformat()}.json"
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Caché guardada en: %s", ruta)
    return ruta
