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
import re
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
    from src.pipeline import recolectar_datos
    from src.analyzer.claude_analyzer import ClaudeAnalyzer
    from src.reporter.report_generator import ReportGenerator

    datos_raw = await recolectar_datos(fuente)

    if not datos_raw:
        return json.dumps({"error": "No se encontraron datos. Verifica conexión y configuración."})

    try:
        analyzer = ClaudeAnalyzer()
    except ValueError as exc:
        return json.dumps({"error": str(exc)})

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
    from src.pipeline import recolectar_datos, guardar_cache

    datos = await recolectar_datos(fuente)

    # Guardar caché completa en data/
    dir_datos = Path(os.getenv("DIRECTORIO_DATOS", str(Path(__file__).parent.parent / "data")))
    cache_path = guardar_cache(datos, dir_datos)

    from collections import Counter
    import yaml

    # Cargar keywords políticas desde settings.yaml para filtrar
    settings_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    try:
        with open(settings_path, encoding="utf-8") as f:
            settings = yaml.safe_load(f)
    except FileNotFoundError:
        return json.dumps({
            "error": f"Archivo de configuración no encontrado: {settings_path}. "
                     "Verifica que config/settings.yaml exista."
        })

    keywords_politica = [k.lower() for k in settings.get("keywords_politica", [])]
    categorias = [c.lower() for c in settings.get("categorias", [])]
    terminos_filtro = keywords_politica + categorias + [
        "congres", "ministr", "premier", "fiscal", "corrupci", "eleccion",
        "partido", "voto", "ley ", "decreto", "poder judicial", "tribunal",
        "boluarte", "petro", "gobierno", "presupuest", "reforma",
    ]

    def es_politico(art: dict) -> bool:
        texto = f"{art.get('titulo', '')} {art.get('resumen', '')}".lower()
        return any(t in texto for t in terminos_filtro)

    por_fuente = Counter(d.get("fuente_tipo", "desconocido") for d in datos)

    # Solo artículos políticos, solo títulos + fuente (payload mínimo)
    articulos_politicos = [
        {"titulo": d.get("titulo", ""), "fuente": d.get("fuente", "")}
        for d in datos
        if d.get("fuente_tipo") == "rss" and es_politico(d)
    ]

    keywords_trends = [
        {"keyword": d["keyword"], "score": d.get("score")}
        for d in datos if "google_trends" in d.get("fuente_tipo", "")
    ]

    return json.dumps(
        {
            "total_recolectado": len(datos),
            "total_politico": len(articulos_politicos),
            "cache": str(cache_path),
            "por_fuente": dict(por_fuente),
            "nota": "Cache completa guardada. Artículos filtrados por relevancia política.",
            "articulos_politicos": articulos_politicos,
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
    Si no hay caché para esa fecha, retorna un error indicando que se debe
    usar `ejecutar_analisis` primero para recolectar los datos.

    Parámetros:
        fecha: Fecha en formato YYYY-MM-DD. Si está vacío, usa hoy.

    Retorna las rutas de los archivos generados.
    """
    if fecha and not _validar_fecha(fecha):
        return json.dumps({"error": "Formato de fecha inválido. Usar YYYY-MM-DD."})

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

    try:
        analyzer = ClaudeAnalyzer()
    except ValueError as exc:
        return json.dumps({"error": str(exc)})

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
_ARCHIVOS_PERMITIDOS = {
    "00_resumen.md",
    "01_tendencias.md",
    "02_analisis.md",
    "03_posts_redes.md",
    "04_fuentes.md",
}

_RE_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _validar_fecha(fecha: str) -> bool:
    return bool(_RE_FECHA.match(fecha))


def _ruta_segura(base: Path, *partes: str) -> Path | None:
    """Resuelve la ruta y verifica que sea descendiente del directorio base."""
    try:
        ruta = base.resolve()
        candidata = (base / Path(*partes)).resolve()
        if candidata.is_relative_to(ruta):
            return candidata
    except Exception:
        pass
    return None


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
    if archivo not in _ARCHIVOS_PERMITIDOS:
        return json.dumps({
            "error": f"Archivo no permitido: '{archivo}'. "
                     f"Opciones válidas: {sorted(_ARCHIVOS_PERMITIDOS)}"
        })

    dir_reportes = Path(DIRECTORIO_REPORTES)

    if not fecha:
        if not dir_reportes.exists():
            return "No hay informes generados. Usa ejecutar_analisis primero."
        carpetas = sorted(
            [d for d in dir_reportes.iterdir() if d.is_dir()],
            reverse=True,
        )
        if not carpetas:
            return "No hay informes generados. Usa ejecutar_analisis primero."
        carpeta = carpetas[0]
    else:
        if not _validar_fecha(fecha):
            return json.dumps({"error": "Formato de fecha inválido. Usar YYYY-MM-DD."})
        carpeta = dir_reportes / fecha

    ruta = _ruta_segura(dir_reportes, carpeta.name, archivo)
    if ruta is None:
        return json.dumps({"error": "Ruta no permitida."})

    if not ruta.exists():
        return f"Archivo no encontrado: {ruta}"

    return ruta.read_text(encoding="utf-8")


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
    elif not _validar_fecha(fecha):
        return json.dumps({"error": "Formato de fecha inválido. Usar YYYY-MM-DD."})

    dir_base_reportes = Path(DIRECTORIO_REPORTES)
    ruta_destino = _ruta_segura(dir_base_reportes, fecha)
    if ruta_destino is None:
        return json.dumps({"error": "Ruta no permitida."})

    dir_reportes = ruta_destino
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
