"""
Recolector de artículos desde feeds RSS de medios peruanos de política.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import httpx
import yaml

logger = logging.getLogger(__name__)

SETTINGS_PATH = Path(__file__).parent.parent.parent / "config" / "settings.yaml"


def _cargar_config_rss() -> tuple[list[dict], int]:
    """Carga feeds y ventana de tiempo desde settings.yaml en una sola lectura."""
    with open(SETTINGS_PATH, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("rss_feeds", []), cfg.get("rss_horas_atras", 48)


def _parsear_fecha(entrada) -> datetime | None:
    """Intenta extraer la fecha de publicación de una entrada RSS."""
    for campo in ("published_parsed", "updated_parsed", "created_parsed"):
        t = getattr(entrada, campo, None)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    return None


async def _fetch_feed(client: httpx.AsyncClient, feed: dict, horas_atras: int) -> list[dict]:
    """Descarga y parsea un feed RSS, filtrando por antigüedad."""
    name = feed["name"]
    url = feed["url"]
    limite = datetime.now(timezone.utc) - timedelta(hours=horas_atras)
    articulos = []
    try:
        resp = await client.get(url, timeout=15.0, follow_redirects=True)
        resp.raise_for_status()
        parsed = feedparser.parse(resp.text)
        for entrada in parsed.entries:
            fecha = _parsear_fecha(entrada)
            if fecha is None:
                logger.debug(
                    "Artículo sin fecha en %s: '%s' — incluido sin filtrar por antigüedad",
                    name, getattr(entrada, "title", "sin título"),
                )
            elif fecha < limite:
                continue
            articulos.append({
                "titulo": getattr(entrada, "title", ""),
                "url": getattr(entrada, "link", ""),
                "resumen": getattr(entrada, "summary", ""),
                "fuente": name,
                "fecha": fecha.isoformat() if fecha else None,
                "fuente_tipo": "rss",
            })
        logger.info("RSS %s: %d artículos recientes", name, len(articulos))
    except Exception as exc:
        logger.warning("Error al leer RSS %s (%s): %s", name, url, exc)
    return articulos


class RSSCollector:
    """Recolecta artículos de política desde feeds RSS de medios peruanos."""

    async def recolectar_todo(self) -> list[dict]:
        """Descarga todos los feeds en paralelo y retorna los artículos recientes."""
        feeds, horas_atras = _cargar_config_rss()
        if not feeds:
            logger.warning("No hay feeds RSS configurados en settings.yaml")
            return []
        async with httpx.AsyncClient(
            headers={"User-Agent": "TrendsPoliticaBot/1.0"},
        ) as client:
            resultados = await asyncio.gather(
                *[_fetch_feed(client, f, horas_atras) for f in feeds]
            )
        todos = [art for lista in resultados for art in lista]
        logger.info("RSS total: %d artículos recolectados", len(todos))
        return todos
