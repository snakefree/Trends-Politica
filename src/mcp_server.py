"""
Servidor MCP (Model Context Protocol) para el agente Trends-Política.

Expone herramientas para monitorear tendencias políticas peruanas y generar informes.

Configuración en Claude Code (%APPDATA%\\Claude\\claude_desktop_config.json):
{
  "mcpServers": {
    "trends-politica": {
      "command": "D:/Development/Trends-Política/venv/Scripts/python.exe",
      "args": ["-m", "src.mcp_server"],
      "cwd": "D:/Development/Trends-Política"
    }
  }
}

Reinicia Claude Code después de guardar la configuración.
"""
import asyncio
import json
import logging
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger(__name__)

DIRECTORIO_REPORTES = os.getenv(
    "DIRECTORIO_REPORTES",
    str(Path(__file__).parent.parent / "reports"),
)

mcp = FastMCP(
    "Trends-Política",
    instructions=(
        "Herramientas para monitorear tendencias políticas peruanas en redes sociales y medios. "
        "Analiza Google Trends y RSS de medios peruanos, genera informes Markdown modulares "
        "con análisis de temas y borradores de posts para Instagram, Facebook, X y TikTok."
    ),
)


# ---------------------------------------------------------------------------
# Herramienta 1: Pipeline completo
# ---------------------------------------------------------------------------
@mcp.tool()
async def ejecutar_analisis(
    fuente: str = "all",
) -> str:
    """
    Ejecuta el pipeline completo: recolecta datos → analiza con Claude → genera informe.

    Parámetros:
        fuente: Fuente de datos a usar. Opciones: 'all', 'rss', 'google_trends'.
                Por defecto usa todas las fuentes disponibles.

    Retorna un JSON con las rutas de los 5 archivos Markdown generados.
    Puede tardar 1-3 minutos dependiendo de la cantidad de datos.
    """
    from src.collectors.rss_collector import RSSCollector
    from src.collectors.twitter_collector import TwitterCollector
    from src.collectors.tiktok_collector import TikTokCollector
    from src.analyzer.claude_analyzer import ClaudeAnalyzer
    from src.reporter.report_generator import ReportGenerator

    datos_raw = []

    if fuente in ("all", "rss"):
        rss = RSSCollector()
        datos_raw.extend(await rss.collect_all())

    if fuente in ("all", "google_trends"):
        try:
            from src.collectors.google_trends_collector import GoogleTrendsCollector
            gt = GoogleTrendsCollector()
            datos_raw.extend(await asyncio.to_thread(gt.collect_all))
        except ImportError:
            pass

    if fuente in ("all", "twitter"):
        tw = TwitterCollector()
        datos_raw.extend(await asyncio.to_thread(tw.collect_all))

    if fuente in ("all", "tiktok"):
        tt = TikTokCollector()
        datos_raw.extend(await asyncio.to_thread(tt.collect_all))

    if not datos_raw:
        return json.dumps({"error": "No se encontraron datos. Verifica conexión y configuración."})

    analyzer = ClaudeAnalyzer()
    resultado = await asyncio.to_thread(analyzer.analizar_y_generar_posts, datos_raw)

    reporter = ReportGenerator()
    archivos = await asyncio.to_thread(reporter.generar, resultado, datos_raw)

    return json.dumps(
        {
            "fecha": resultado.fecha,
            "temas_identificados": len(resultado.temas),
            "items_recolectados": len(datos_raw),
            "archivos": {k: str(v) for k, v in archivos.items()},
        },
        ensure_ascii=False,
        indent=2,
    )


# ---------------------------------------------------------------------------
# Herramienta 2: Solo recolección (sin análisis Claude)
# ---------------------------------------------------------------------------
@mcp.tool()
async def obtener_tendencias(
    fuente: str = "all",
) -> str:
    """
    Recolecta datos de tendencias, guarda caché en data/ y retorna TODOS los artículos
    y keywords para que Claude Code pueda analizarlos directamente en el chat.

    Parámetros:
        fuente: 'all', 'rss', 'google_trends', 'twitter', 'tiktok'

    Retorna todos los títulos RSS y keywords de Google Trends recolectados,
    más la ruta del archivo de caché guardado.
    """
    from src.collectors.rss_collector import RSSCollector
    from src.collectors.twitter_collector import TwitterCollector
    from src.collectors.tiktok_collector import TikTokCollector

    datos = []

    if fuente in ("all", "rss"):
        rss = RSSCollector()
        datos.extend(await rss.collect_all())

    if fuente in ("all", "google_trends"):
        try:
            from src.collectors.google_trends_collector import GoogleTrendsCollector
            gt = GoogleTrendsCollector()
            datos.extend(await asyncio.to_thread(gt.collect_all))
        except ImportError:
            pass

    if fuente in ("all", "twitter"):
        tw = TwitterCollector()
        datos.extend(await asyncio.to_thread(tw.collect_all))

    if fuente in ("all", "tiktok"):
        tt = TikTokCollector()
        datos.extend(await asyncio.to_thread(tt.collect_all))

    # Guardar caché completa en data/
    dir_datos = Path(os.getenv("DIRECTORIO_DATOS", str(Path(__file__).parent.parent / "data")))
    dir_datos.mkdir(parents=True, exist_ok=True)
    cache_path = dir_datos / f"raw_{date.today().isoformat()}.json"
    cache_path.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    # Devolver TODOS los artículos RSS (titulo + resumen breve + fuente)
    from collections import Counter
    por_fuente = Counter(d.get("source", "desconocido") for d in datos)

    articulos_rss = [
        {
            "titulo": d.get("titulo", ""),
            "fuente": d.get("fuente", ""),
            "resumen": (d.get("resumen") or "")[:200],
        }
        for d in datos if d.get("source") == "rss"
    ]

    keywords_trends = [
        {"keyword": d["keyword"], "score": d.get("score"), "fuente": d.get("source")}
        for d in datos if "google_trends" in d.get("source", "")
    ]

    return json.dumps(
        {
            "total": len(datos),
            "cache": str(cache_path),
            "por_fuente": dict(por_fuente),
            "articulos_rss": articulos_rss,
            "keywords_google_trends": keywords_trends,
        },
        ensure_ascii=False,
        indent=2,
    )


# ---------------------------------------------------------------------------
# Herramienta 3: Generar informe desde caché
# ---------------------------------------------------------------------------
@mcp.tool()
async def generar_informe(fecha: str = "") -> str:
    """
    Genera el análisis e informe para una fecha específica usando datos en caché.
    Si no hay caché para esa fecha, ejecuta la recolección primero.

    Parámetros:
        fecha: Fecha en formato YYYY-MM-DD. Si está vacío, usa hoy.

    Retorna las rutas de los archivos generados.
    """
    if not fecha:
        fecha = date.today().isoformat()

    dir_datos = Path(os.getenv("DIRECTORIO_DATOS", str(Path(__file__).parent.parent / "data")))
    cache_file = dir_datos / f"raw_{fecha}.json"

    if cache_file.exists():
        datos_raw = json.loads(cache_file.read_text(encoding="utf-8"))
    else:
        return json.dumps({
            "error": f"No hay datos en caché para {fecha}. Usa ejecutar_analisis para recolectar."
        })

    from src.analyzer.claude_analyzer import ClaudeAnalyzer
    from src.reporter.report_generator import ReportGenerator

    analyzer = ClaudeAnalyzer()
    resultado = await asyncio.to_thread(analyzer.analizar_y_generar_posts, datos_raw)

    reporter = ReportGenerator()
    archivos = await asyncio.to_thread(reporter.generar, resultado, datos_raw)

    return json.dumps(
        {
            "fecha": resultado.fecha,
            "temas": len(resultado.temas),
            "archivos": {k: str(v) for k, v in archivos.items()},
        },
        ensure_ascii=False,
        indent=2,
    )


# ---------------------------------------------------------------------------
# Herramienta 4: Listar informes generados
# ---------------------------------------------------------------------------
@mcp.tool()
def listar_informes() -> str:
    """
    Lista todos los informes generados con sus fechas y archivos disponibles.

    Retorna un JSON con la lista de informes ordenados de más reciente a más antiguo.
    """
    dir_reportes = Path(DIRECTORIO_REPORTES)
    if not dir_reportes.exists():
        return json.dumps({"total": 0, "informes": []})

    informes = []
    for carpeta in sorted(dir_reportes.iterdir(), reverse=True):
        if not carpeta.is_dir():
            continue
        archivos = [f.name for f in sorted(carpeta.glob("*.md"))]
        informes.append({"fecha": carpeta.name, "archivos": archivos})

    return json.dumps(
        {"total": len(informes), "informes": informes},
        ensure_ascii=False,
        indent=2,
    )


# ---------------------------------------------------------------------------
# Herramienta 5: Leer un informe específico
# ---------------------------------------------------------------------------
@mcp.tool()
def leer_informe(fecha: str = "", archivo: str = "00_resumen.md") -> str:
    """
    Lee el contenido de un archivo Markdown de un informe específico.

    Parámetros:
        fecha: Fecha del informe en formato YYYY-MM-DD. Si está vacío, usa el más reciente.
        archivo: Nombre del archivo a leer. Opciones:
                 '00_resumen.md', '01_tendencias.md', '02_analisis.md',
                 '03_posts_redes.md', '04_fuentes.md'

    Retorna el contenido del archivo Markdown.
    """
    dir_reportes = Path(DIRECTORIO_REPORTES)

    if not fecha:
        carpetas = sorted(
            [d for d in dir_reportes.iterdir() if d.is_dir()],
            reverse=True,
        )
        if not carpetas:
            return "No hay informes generados. Usa ejecutar_analisis primero."
        carpeta = carpetas[0]
    else:
        carpeta = dir_reportes / fecha

    path = carpeta / archivo
    if not path.exists():
        return f"Archivo no encontrado: {path}"

    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Herramienta 6: Guardar informe generado manualmente por Claude Code
# ---------------------------------------------------------------------------
@mcp.tool()
def guardar_informe_manual(
    resumen: str,
    tendencias: str,
    analisis: str,
    posts_redes: str,
    fuentes: str,
    fecha: str = "",
) -> str:
    """
    Escribe los 5 archivos Markdown del informe con contenido generado por Claude Code.
    Usar cuando Claude Code hace el análisis directamente en el chat (sin API key propia).

    Parámetros:
        resumen: Contenido Markdown para 00_resumen.md (headline + top 3 temas)
        tendencias: Contenido Markdown para 01_tendencias.md (ranking completo)
        analisis: Contenido Markdown para 02_analisis.md (análisis profundo)
        posts_redes: Contenido Markdown para 03_posts_redes.md (borradores por plataforma)
        fuentes: Contenido Markdown para 04_fuentes.md (URLs y metadatos)
        fecha: Fecha YYYY-MM-DD. Si está vacío, usa hoy.

    Retorna las rutas de los archivos creados.
    """
    if not fecha:
        fecha = date.today().isoformat()

    dir_reportes = Path(DIRECTORIO_REPORTES) / fecha
    dir_reportes.mkdir(parents=True, exist_ok=True)

    archivos = {
        "00_resumen.md": resumen,
        "01_tendencias.md": tendencias,
        "02_analisis.md": analisis,
        "03_posts_redes.md": posts_redes,
        "04_fuentes.md": fuentes,
    }

    rutas = {}
    for nombre, contenido in archivos.items():
        path = dir_reportes / nombre
        path.write_text(contenido, encoding="utf-8")
        rutas[nombre] = str(path)

    # Actualizar índice en reports/README.md
    readme = Path(DIRECTORIO_REPORTES) / "README.md"
    indice = "# Índice de informes — Trends-Política\n\n"
    for carpeta in sorted(Path(DIRECTORIO_REPORTES).iterdir(), reverse=True):
        if carpeta.is_dir():
            indice += f"- [{carpeta.name}]({carpeta.name}/00_resumen.md)\n"
    readme.write_text(indice, encoding="utf-8")

    return json.dumps(
        {"fecha": fecha, "archivos_creados": rutas},
        ensure_ascii=False,
        indent=2,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
