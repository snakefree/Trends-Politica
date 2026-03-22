# CLAUDE.md — Trends-Política

Agente de monitoreo de tendencias políticas peruanas en redes sociales y medios digitales.

## Propósito

Recolecta datos de Google Trends y RSS de medios peruanos, usa la API de Claude para analizar
los temas políticos más candentes, y genera informes modulares en Markdown listos para elaborar
posts en Instagram, Facebook, X (Twitter) y TikTok.

## Comandos CLI

```powershell
# Activar entorno virtual primero
venv\Scripts\activate

# Ejecutar pipeline completo (recolección → análisis → informe)
python main.py run

# Ejecutar solo con una fuente de datos
python main.py run --source rss
python main.py run --source google_trends

# Ver el último informe generado
python main.py report

# Configurar ejecución automática
python main.py schedule --interval daily
python main.py schedule --interval weekly

# Ver estado del scheduler
python main.py status
```

## Variables de entorno requeridas

Copiar `.env.example` a `.env` y configurar:

| Variable | Descripción | Requerida |
|---|---|---|
| `ANTHROPIC_API_KEY` | Clave API de Anthropic | Sí |
| `CLAUDE_MODEL` | Modelo a usar (default: claude-sonnet-4-6) | No |
| `DIRECTORIO_REPORTES` | Ruta de salida de informes | No |
| `DIRECTORIO_DATOS` | Ruta de caché de datos crudos | No |

## Estructura del proyecto

```
Trends-Política/
├── main.py                    # CLI entry point
├── config/settings.yaml       # Keywords, fuentes RSS, schedule
├── src/
│   ├── collectors/            # Recolectores de datos
│   │   ├── rss_collector.py          # RSS de medios peruanos
│   │   ├── google_trends_collector.py # Google Trends vía pytrends
│   │   ├── twitter_collector.py      # X/Twitter (opcional)
│   │   └── tiktok_collector.py       # TikTok (opcional)
│   ├── analyzer/
│   │   └── claude_analyzer.py  # Análisis con Claude API
│   ├── reporter/
│   │   └── report_generator.py # Generador de MD modulares
│   ├── scheduler/
│   │   └── scheduler.py        # APScheduler
│   └── mcp_server.py           # Servidor MCP para Claude Code
├── reports/                   # Informes generados (gitignored)
└── data/                      # Caché de datos (gitignored)
```

## Informes modulares — Estructura

Cada ejecución genera una carpeta `reports/YYYY-MM-DD/` con:

| Archivo | Contenido |
|---|---|
| `00_resumen.md` | Headline + top 3 temas (lectura rápida) |
| `01_tendencias.md` | Ranking completo de tendencias con métricas |
| `02_analisis.md` | Análisis profundo por tema (contexto, actores) |
| `03_posts_redes.md` | Borradores de posts por plataforma y tema |
| `04_fuentes.md` | URLs fuente, timestamps, volúmenes de búsqueda |

## Scrapers opcionales

Los scrapers de Twitter/X y TikTok no están instalados por defecto (graceful fallback).
Para habilitarlos:

```powershell
# Twitter/X (sin API oficial)
pip install ntscraper

# TikTok (requiere Playwright con Chromium)
pip install TikTokApi
playwright install chromium
```

Agregar credenciales opcionales en `.env`:
```
TWITTER_USERNAME=tu_usuario
TWITTER_PASSWORD=tu_contraseña
```

## Servidor MCP para Claude Code

Permite invocar el agente directamente desde el chat de Claude Code.

Agregar en `%APPDATA%\Claude\claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "trends-politica": {
      "command": "D:/Development/Trends-Política/venv/Scripts/python.exe",
      "args": ["-m", "src.mcp_server"],
      "cwd": "D:/Development/Trends-Política"
    }
  }
}
```

Reiniciar Claude Code. Herramientas disponibles: `ejecutar_analisis`, `obtener_tendencias`,
`generar_informe`, `listar_informes`, `leer_informe`.

## Instalación

```powershell
cd D:/Development/Trends-Política
py -3 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Editar .env con tu ANTHROPIC_API_KEY
```
