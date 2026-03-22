"""
Trends-Política — CLI principal
Monitoreo de tendencias políticas peruanas en redes sociales y medios.

Uso:
    python main.py run                        # Pipeline completo
    python main.py run --source rss           # Solo RSS
    python main.py run --source google_trends # Solo Google Trends
    python main.py report                     # Ver último informe
    python main.py schedule --interval daily  # Iniciar scheduler
    python main.py status                     # Estado del scheduler
"""
import json
import logging
import os
import sys
from datetime import date
from pathlib import Path

import click
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _dir_reportes() -> Path:
    base = os.getenv("DIRECTORIO_REPORTES")
    if base:
        return Path(base)
    return Path(__file__).parent / "reports"


def _guardar_cache(datos: list) -> Path:
    """Guarda los datos crudos en data/raw_YYYY-MM-DD.json para reutilización."""
    dir_datos = Path(os.getenv("DIRECTORIO_DATOS", str(Path(__file__).parent / "data")))
    dir_datos.mkdir(parents=True, exist_ok=True)
    path = dir_datos / f"raw_{date.today().isoformat()}.json"
    path.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _ultimo_informe() -> Path | None:
    """Retorna la carpeta del informe más reciente."""
    dr = _dir_reportes()
    if not dr.exists():
        return None
    carpetas = sorted(
        [d for d in dr.iterdir() if d.is_dir()],
        reverse=True,
    )
    return carpetas[0] if carpetas else None


@click.group()
def cli():
    """Agente de tendencias políticas peruanas."""
    pass


@cli.command()
@click.option(
    "--source",
    type=click.Choice(["all", "rss", "google_trends", "twitter", "tiktok"]),
    default="all",
    show_default=True,
    help="Fuente de datos a usar.",
)
@click.option(
    "--solo-recolectar",
    is_flag=True,
    default=False,
    help="Solo recolectar datos, sin análisis Claude (útil para pruebas).",
)
def run(source: str, solo_recolectar: bool):
    """Ejecuta el pipeline de tendencias (recolección → análisis → informe)."""
    import asyncio
    from src.collectors.rss_collector import RSSCollector
    from src.collectors.twitter_collector import TwitterCollector
    from src.collectors.tiktok_collector import TikTokCollector

    datos_raw = []

    if source in ("all", "rss"):
        click.echo("Recolectando RSS...")
        rss = RSSCollector()
        datos_raw.extend(asyncio.run(rss.collect_all()))

    if source in ("all", "google_trends"):
        click.echo("Consultando Google Trends...")
        try:
            from src.collectors.google_trends_collector import GoogleTrendsCollector
            gt = GoogleTrendsCollector()
            datos_raw.extend(gt.collect_all())
        except ImportError as e:
            click.echo(f"  [aviso] Google Trends no disponible: {e}", err=True)

    if source in ("all", "twitter"):
        click.echo("Recolectando Twitter/X...")
        tw = TwitterCollector()
        datos_raw.extend(tw.collect_all())

    if source in ("all", "tiktok"):
        click.echo("Recolectando TikTok...")
        tt = TikTokCollector()
        datos_raw.extend(tt.collect_all())

    click.echo(f"Total recolectado: {len(datos_raw)} items")

    if not datos_raw:
        click.echo("No se encontraron datos. Verifica tu conexión y la configuración.", err=True)
        sys.exit(1)

    cache_path = _guardar_cache(datos_raw)
    click.echo(f"Datos guardados en: {cache_path}")

    if solo_recolectar:
        click.echo("Modo --solo-recolectar: análisis omitido.")
        return

    # Verificar API key antes de llamar a Claude
    if not os.getenv("ANTHROPIC_API_KEY"):
        click.echo(
            "Error: ANTHROPIC_API_KEY no configurada.\n"
            "Copia .env.example a .env y agrega tu clave.",
            err=True,
        )
        sys.exit(1)

    click.echo("Analizando con Claude...")
    from src.analyzer.claude_analyzer import ClaudeAnalyzer
    analyzer = ClaudeAnalyzer()
    resultado = analyzer.analizar_y_generar_posts(datos_raw)

    click.echo(f"Temas identificados: {len(resultado.temas)}")
    click.echo("Generando informes Markdown...")

    from src.reporter.report_generator import ReportGenerator
    reporter = ReportGenerator()
    archivos = reporter.generar(resultado, datos_raw)

    click.echo("\n Informe generado:")
    for nombre, path in archivos.items():
        click.echo(f"  {nombre:12s} → {path}")

    resumen_path = archivos.get("resumen")
    if resumen_path:
        click.echo(f"\nResumen ejecutivo: {resumen_path}")


@cli.command()
def report():
    """Muestra la ruta del último informe generado."""
    ultimo = _ultimo_informe()
    if not ultimo:
        click.echo("No hay informes generados aún. Ejecuta: python main.py run")
        return
    click.echo(f"Último informe: {ultimo}")
    for md in sorted(ultimo.glob("*.md")):
        click.echo(f"  {md.name}")


@cli.command()
@click.option(
    "--interval",
    type=click.Choice(["hourly", "daily", "weekly"]),
    default="daily",
    show_default=True,
    help="Frecuencia de ejecución automática.",
)
@click.option(
    "--hora",
    default="08:00",
    show_default=True,
    help="Hora de ejecución diaria/semanal (HH:MM, zona Lima).",
)
@click.option(
    "--schtasks",
    is_flag=True,
    default=False,
    help="Mostrar comando schtasks para Windows Task Scheduler.",
)
def schedule(interval: str, hora: str, schtasks: bool):
    """Inicia el scheduler automático (proceso persistente)."""
    from src.scheduler.scheduler import iniciar_scheduler, generar_comando_schtasks

    if schtasks:
        cmd = generar_comando_schtasks(interval, hora)
        click.echo("Ejecuta este comando en PowerShell como Administrador:")
        click.echo(f"\n  {cmd}\n")
        click.echo("Para eliminar la tarea: schtasks /DELETE /TN \"TrendsPolitica\" /F")
        return

    click.echo(f"Iniciando scheduler: {interval} a las {hora} (Lima)")
    click.echo("Ctrl+C para detener.")
    iniciar_scheduler(interval, hora)


@cli.command()
def status():
    """Muestra el estado del scheduler y el último informe."""
    from src.scheduler.scheduler import obtener_estado
    estado = obtener_estado()
    click.echo("=== Estado del scheduler ===")
    for k, v in estado.items():
        click.echo(f"  {k}: {v}")
    click.echo("\n=== Último informe ===")
    ultimo = _ultimo_informe()
    if ultimo:
        click.echo(f"  Carpeta: {ultimo}")
        archivos = list(ultimo.glob("*.md"))
        click.echo(f"  Archivos: {len(archivos)}")
    else:
        click.echo("  Ninguno generado aún.")


if __name__ == "__main__":
    cli()
