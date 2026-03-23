"""
Recolector de tendencias desde Google Trends usando pytrends.
"""
import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

SETTINGS_PATH = Path(__file__).parent.parent.parent / "config" / "settings.yaml"

try:
    from pytrends.request import TrendReq
    _PYTRENDS_DISPONIBLE = True
except ImportError:
    _PYTRENDS_DISPONIBLE = False
    logger.warning("pytrends no está instalado. Ejecuta: pip install pytrends")


def _cargar_config() -> dict:
    with open(SETTINGS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


class GoogleTrendsCollector:
    """Recolecta tendencias de búsqueda en Perú desde Google Trends."""

    def __init__(self):
        if not _PYTRENDS_DISPONIBLE:
            raise ImportError("pytrends no está instalado: pip install pytrends")
        cfg = _cargar_config()
        self.geo = cfg.get("geo", "PE")
        self.timeframe = cfg.get("timeframe", "now 7-d")
        self.keywords = cfg.get("keywords_politica", [])
        self.pytrends = TrendReq(hl="es-419", tz=300, timeout=(5, 25))  # UTC-5 Lima

    def get_trending_searches(self) -> list[dict]:
        """Retorna las búsquedas de tendencia en tiempo real en Perú."""
        try:
            df = self.pytrends.realtime_trending_searches(pn=self.geo)
            tendencias = []
            for _, row in df.iterrows():
                keyword = row.get("title", "") or row.get("entityNames", "")
                if isinstance(keyword, list):
                    keyword = ", ".join(keyword)
                if keyword:
                    tendencias.append({
                        "keyword": str(keyword),
                        "score": None,
                        "related": [],
                        "source": "google_trends_daily",
                    })
            logger.info("Google Trends realtime: %d tendencias", len(tendencias))
            return tendencias
        except Exception as exc:
            logger.info("Google Trends realtime no disponible (%s) — usando solo interest_over_time", exc)
            return []

    def get_interest_over_time(self, keywords: list[str] | None = None) -> list[dict]:
        """
        Retorna el interés relativo de las keywords configuradas en el período definido.
        Procesa en lotes de 5 (límite de pytrends).
        """
        kws = keywords or self.keywords
        if not kws:
            return []
        resultados = []
        # pytrends acepta máximo 5 keywords por llamada
        for i in range(0, len(kws), 5):
            lote = kws[i : i + 5]
            try:
                self.pytrends.build_payload(lote, geo=self.geo, timeframe=self.timeframe)
                df = self.pytrends.interest_over_time()
                if df.empty:
                    continue
                for kw in lote:
                    if kw not in df.columns:
                        continue
                    score = int(df[kw].mean())
                    resultados.append({
                        "keyword": kw,
                        "score": score,
                        "related": [],
                        "source": "google_trends_interest",
                    })
            except Exception as exc:
                logger.warning("Error en interest_over_time (lote %s): %s", lote, exc)
        logger.info("Google Trends interest: %d keywords procesadas", len(resultados))
        return resultados

    def get_related_queries(self, keyword: str) -> list[str]:
        """Retorna queries relacionadas (top) para una keyword dada."""
        try:
            self.pytrends.build_payload([keyword], geo=self.geo, timeframe=self.timeframe)
            related = self.pytrends.related_queries()
            top = related.get(keyword, {}).get("top")
            if top is not None and not top.empty:
                return top["query"].tolist()[:10]
        except Exception as exc:
            logger.warning("Error en related_queries (%s): %s", keyword, exc)
        return []

    def collect_all(self) -> list[dict]:
        """Pipeline completo: trending + interest sobre keywords configuradas."""
        trending = self.get_trending_searches()
        interest = self.get_interest_over_time()
        return trending + interest
