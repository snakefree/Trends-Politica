"""
Scheduler para ejecución automática del pipeline de tendencias.
Usa APScheduler con persistencia en data/scheduler_state.json.
"""
import json
import logging
import os
import signal
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

logger = logging.getLogger(__name__)

try:
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    _APSCHEDULER_DISPONIBLE = True
except ImportError:
    _APSCHEDULER_DISPONIBLE = False


def _dir_datos() -> Path:
    base = os.getenv("DIRECTORIO_DATOS")
    if base:
        return Path(base)
    return Path(__file__).parent.parent.parent / "data"


STATE_FILE = _dir_datos() / "scheduler_state.json"


def _guardar_estado(config: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def _cargar_estado() -> dict | None:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


def ejecutar_pipeline() -> dict:
    """
    Pipeline completo: recolección → análisis → generación de informe.
    Retorna un dict con los paths de los archivos generados.
    """
    import asyncio
    from src.collectors.google_trends_collector import GoogleTrendsCollector
    from src.collectors.rss_collector import RSSCollector
    from src.collectors.twitter_collector import TwitterCollector
    from src.collectors.tiktok_collector import TikTokCollector
    from src.analyzer.claude_analyzer import ClaudeAnalyzer
    from src.reporter.report_generator import ReportGenerator

    logger.info("=== Iniciando pipeline de tendencias políticas ===")
    datos_raw = []

    # 1. Recolección RSS (siempre disponible)
    logger.info("Paso 1/4: Recolectando RSS...")
    rss = RSSCollector()
    datos_raw.extend(asyncio.run(rss.collect_all()))

    # 2. Google Trends
    logger.info("Paso 2/4: Consultando Google Trends...")
    try:
        gt = GoogleTrendsCollector()
        datos_raw.extend(gt.collect_all())
    except ImportError as e:
        logger.warning("Google Trends no disponible: %s", e)

    # 3. Twitter/X (opcional)
    logger.info("Paso 3/4: Recolectando Twitter/X (si disponible)...")
    tw = TwitterCollector()
    datos_raw.extend(tw.collect_all())

    # 4. TikTok (opcional)
    logger.info("Paso 4/4: Recolectando TikTok (si disponible)...")
    tt = TikTokCollector()
    datos_raw.extend(tt.collect_all())

    logger.info("Total de items recolectados: %d", len(datos_raw))

    if not datos_raw:
        logger.error("No se recolectaron datos. Abortando análisis.")
        return {}

    # 5. Análisis con Claude
    logger.info("Analizando tendencias con Claude...")
    analyzer = ClaudeAnalyzer()
    resultado = analyzer.analizar_y_generar_posts(datos_raw)

    # 6. Generar informes MD
    logger.info("Generando informes Markdown...")
    reporter = ReportGenerator()
    archivos = reporter.generar(resultado, datos_raw)

    logger.info("=== Pipeline completado. Temas identificados: %d ===", len(resultado.temas))
    return {k: str(v) for k, v in archivos.items()}


def iniciar_scheduler(interval: str = "daily", hora: str = "08:00") -> None:
    """
    Inicia el scheduler bloqueante. Ejecuta el pipeline según el intervalo.
    - interval: 'hourly', 'daily', 'weekly'
    - hora: 'HH:MM' (solo para daily/weekly)
    """
    if not _APSCHEDULER_DISPONIBLE:
        logger.error("APScheduler no está instalado: pip install apscheduler")
        sys.exit(1)

    # Guardar configuración
    estado = {"interval": interval, "hora": hora}
    _guardar_estado(estado)

    scheduler = BlockingScheduler(timezone="America/Lima")

    if interval == "hourly":
        trigger = IntervalTrigger(hours=1)
        logger.info("Scheduler configurado: cada hora")
    elif interval == "weekly":
        hora_h, hora_m = hora.split(":")
        trigger = CronTrigger(day_of_week="mon", hour=int(hora_h), minute=int(hora_m))
        logger.info("Scheduler configurado: lunes a las %s (Lima)", hora)
    else:  # daily
        hora_h, hora_m = hora.split(":")
        trigger = CronTrigger(hour=int(hora_h), minute=int(hora_m))
        logger.info("Scheduler configurado: diariamente a las %s (Lima)", hora)

    scheduler.add_job(ejecutar_pipeline, trigger, id="pipeline_tendencias")

    def _salir(sig, frame):
        logger.info("Deteniendo scheduler...")
        scheduler.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, _salir)
    signal.signal(signal.SIGTERM, _salir)

    logger.info("Scheduler activo. Ctrl+C para detener.")
    scheduler.start()


def obtener_estado() -> dict:
    """Retorna el estado guardado del scheduler, o un dict vacío."""
    return _cargar_estado() or {"estado": "no configurado"}


def generar_comando_schtasks(interval: str = "daily", hora: str = "08:00") -> str:
    """
    Genera el comando schtasks de Windows para ejecutar el pipeline automáticamente
    sin necesitar mantener un proceso Python activo.
    """
    proyecto = Path(__file__).parent.parent.parent
    python_exe = proyecto / "venv" / "Scripts" / "python.exe"
    main_py = proyecto / "main.py"

    if interval == "daily":
        schedule_type = f"/SC DAILY /ST {hora}"
    elif interval == "weekly":
        schedule_type = f"/SC WEEKLY /D MON /ST {hora}"
    else:
        schedule_type = "/SC HOURLY"

    return (
        f'schtasks /CREATE /TN "TrendsPolitica" '
        f'/TR "\\"{python_exe}\\" \\"{main_py}\\" run" '
        f"{schedule_type} /F"
    )
