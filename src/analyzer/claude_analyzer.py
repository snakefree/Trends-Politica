"""
Motor de análisis de tendencias políticas usando la API de Claude.
"""
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

logger = logging.getLogger(__name__)

MODELO_DEFAULT = "claude-sonnet-4-6"


@dataclass
class TemaAnalizado:
    titulo: str
    relevancia: int          # 1-10
    resumen: str
    contexto: str
    actores: list[str]
    fuentes_relacionadas: list[str]
    categoria: str


@dataclass
class AnalisisResult:
    fecha: str
    temas: list[TemaAnalizado] = field(default_factory=list)
    narrativa_general: str = ""
    recomendaciones: str = ""
    posts: dict[str, list[dict]] = field(default_factory=dict)  # plataforma → lista de posts


def _preparar_datos_para_prompt(datos_raw: list[dict]) -> str:
    """Formatea los datos crudos en texto para el prompt."""
    secciones = []

    # Google Trends
    trends = [d for d in datos_raw if "google_trends" in d.get("source", "")]
    if trends:
        secciones.append("=== GOOGLE TRENDS (Perú) ===")
        for t in trends[:20]:
            score = f" [score: {t['score']}]" if t.get("score") else ""
            related = f" | relacionadas: {', '.join(t['related'][:3])}" if t.get("related") else ""
            secciones.append(f"- {t['keyword']}{score}{related}")

    # RSS
    rss = [d for d in datos_raw if d.get("source") == "rss"]
    if rss:
        secciones.append("\n=== ARTÍCULOS DE MEDIOS PERUANOS (RSS) ===")
        for art in rss[:30]:
            fecha = f" ({art['fecha'][:10]})" if art.get("fecha") else ""
            secciones.append(
                f"[{art['fuente']}]{fecha} {art['titulo']}\n  {art.get('resumen', '')[:200]}"
            )

    # Twitter
    twitter = [d for d in datos_raw if d.get("source") == "twitter"]
    if twitter:
        secciones.append("\n=== TWITTER/X ===")
        for tw in twitter[:15]:
            secciones.append(
                f"@{tw.get('usuario', '?')} ({tw.get('likes', 0)} likes): {tw.get('texto', '')[:200]}"
            )

    # TikTok
    tiktok = [d for d in datos_raw if d.get("source") == "tiktok"]
    if tiktok:
        secciones.append("\n=== TIKTOK ===")
        for tt in tiktok[:10]:
            secciones.append(
                f"#{tt.get('hashtag', '')} | {tt.get('vistas', 0):,} vistas: {tt.get('descripcion', '')[:150]}"
            )

    return "\n".join(secciones)


PROMPT_ANALISIS = """Eres un analista político especializado en Perú. Analiza los siguientes datos \
de tendencias políticas recolectados hoy y produce un análisis estructurado en JSON.

DATOS RECOLECTADOS:
{datos}

Produce un JSON con esta estructura exacta:
{{
  "narrativa_general": "Párrafo de 2-3 oraciones describiendo el panorama político del día",
  "recomendaciones": "Párrafo con recomendaciones para comunicadores políticos",
  "temas": [
    {{
      "titulo": "Nombre corto del tema (máx 10 palabras)",
      "relevancia": 8,
      "resumen": "Qué está pasando en 1-2 oraciones",
      "contexto": "Antecedentes y por qué es importante (2-4 oraciones)",
      "actores": ["Actor 1", "Actor 2"],
      "fuentes_relacionadas": ["nombre medio 1", "nombre medio 2"],
      "categoria": "ejecutivo|legislativo|electoral|economía|seguridad|corrupción|internacional"
    }}
  ]
}}

Ordena los temas de mayor a menor relevancia. Incluye entre 3 y 8 temas.
Responde SOLO con el JSON, sin texto adicional."""


PROMPT_POSTS = """Eres un experto en comunicación política digital en Perú. \
Basándote en este tema político, genera borradores de posts para redes sociales.

TEMA: {titulo}
RESUMEN: {resumen}
CONTEXTO: {contexto}
ACTORES: {actores}

Genera posts optimizados para cada plataforma en formato JSON:
{{
  "X_Twitter": {{
    "texto": "Post de máx 280 caracteres con tono informativo/analítico. Incluye hashtags al final.",
    "hashtags": ["#HashTag1", "#HashTag2"]
  }},
  "Instagram": {{
    "caption": "Caption de hasta 2200 chars. Primer párrafo impactante, luego desarrollo. Emojis moderados.",
    "hashtags": ["#hashtag1", "#hashtag2"]
  }},
  "Facebook": {{
    "texto": "Post largo (500-800 palabras) con contexto completo, análisis y llamado a la reflexión. Formal."
  }},
  "TikTok": {{
    "guion": "Guión de video de 45-60 segundos. Incluye hook inicial, desarrollo y cierre. Tono dinámico.",
    "descripcion": "Descripción corta de 150 chars para la publicación"
  }}
}}

Responde SOLO con el JSON, sin texto adicional."""


class ClaudeAnalyzer:
    """Analiza tendencias políticas peruanas usando la API de Claude."""

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no está configurada en .env")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.modelo = os.getenv("CLAUDE_MODEL", MODELO_DEFAULT)

    def _llamar_claude(self, prompt: str, max_tokens: int = 4096) -> str:
        """Realiza una llamada a la API de Claude y retorna el texto de respuesta."""
        mensaje = self.client.messages.create(
            model=self.modelo,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return mensaje.content[0].text

    def analizar_tendencias(self, datos_raw: list[dict]) -> AnalisisResult:
        """Analiza los datos crudos y retorna un AnalisisResult estructurado."""
        if not datos_raw:
            logger.warning("No hay datos para analizar")
            return AnalisisResult(fecha=date.today().isoformat())

        datos_texto = _preparar_datos_para_prompt(datos_raw)
        prompt = PROMPT_ANALISIS.format(datos=datos_texto)

        logger.info("Enviando %d items a Claude para análisis...", len(datos_raw))
        respuesta_json = self._llamar_claude(prompt, max_tokens=4096)

        try:
            parsed = json.loads(respuesta_json)
        except json.JSONDecodeError as exc:
            logger.error("Claude no retornó JSON válido: %s", exc)
            logger.debug("Respuesta recibida: %s", respuesta_json[:500])
            return AnalisisResult(fecha=date.today().isoformat())

        temas = []
        for t in parsed.get("temas", []):
            temas.append(TemaAnalizado(
                titulo=t.get("titulo", ""),
                relevancia=t.get("relevancia", 5),
                resumen=t.get("resumen", ""),
                contexto=t.get("contexto", ""),
                actores=t.get("actores", []),
                fuentes_relacionadas=t.get("fuentes_relacionadas", []),
                categoria=t.get("categoria", ""),
            ))

        return AnalisisResult(
            fecha=date.today().isoformat(),
            temas=temas,
            narrativa_general=parsed.get("narrativa_general", ""),
            recomendaciones=parsed.get("recomendaciones", ""),
        )

    def generar_posts(self, tema: TemaAnalizado, plataformas: list[str] | None = None) -> dict:
        """
        Genera borradores de posts para un tema dado.
        Retorna un dict plataforma → contenido.
        """
        prompt = PROMPT_POSTS.format(
            titulo=tema.titulo,
            resumen=tema.resumen,
            contexto=tema.contexto,
            actores=", ".join(tema.actores) if tema.actores else "No especificados",
        )
        logger.info("Generando posts para tema: %s", tema.titulo)
        respuesta_json = self._llamar_claude(prompt, max_tokens=3000)

        try:
            return json.loads(respuesta_json)
        except json.JSONDecodeError as exc:
            logger.error("Error al parsear posts de Claude: %s", exc)
            return {}

    def analizar_y_generar_posts(self, datos_raw: list[dict]) -> AnalisisResult:
        """Pipeline completo: análisis + generación de posts para cada tema."""
        resultado = self.analizar_tendencias(datos_raw)
        posts_por_tema = {}
        for tema in resultado.temas:
            posts = self.generar_posts(tema)
            if posts:
                posts_por_tema[tema.titulo] = posts
        resultado.posts = posts_por_tema
        return resultado
