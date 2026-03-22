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
    Recolecta datos de tendencias sin ejecutar el análisis de Claude.
    Útil para explorar los datos crudos o verificar la conectividad.

    Parámetros:
        fuente: 'all', 'rss', 'google_trends', 'twitter', 'tiktok'

    Retorna un resumen de los datos recolectados.
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

    # Resumen por fuente
    from collections import Counter
    por_fuente = Counter(d.get("source", "desconocido") for d in datos)
    muestra_rss = [
        {"titulo": d["titulo"], "fuente": d["fuente"]}
        for d in datos if d.get("source") == "rss"
    ][:10]
    muestra_trends = [
        {"keyword": d["keyword"], "score": d.get("score")}
        for d in datos if "google_trends" in d.get("source", "")
    ][:10]

    return json.dumps(
        {
            "total": len(datos),
            "por_fuente": dict(por_fuente),
            "muestra_rss": muestra_rss,
            "muestra_google_trends": muestra_trends,
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


if __name__ == "__main__":
    mcp.run(transport="stdio")
