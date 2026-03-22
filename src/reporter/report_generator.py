"""
Generador de informes modulares en Markdown.
Cada ejecución crea una carpeta reports/YYYY-MM-DD/ con 5 archivos MD.
"""
import json
import logging
import os
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

logger = logging.getLogger(__name__)


def _dir_reportes() -> Path:
    base = os.getenv("DIRECTORIO_REPORTES")
    if base:
        return Path(base)
    return Path(__file__).parent.parent.parent / "reports"


class ReportGenerator:
    """Genera 5 archivos Markdown modulares por ejecución del pipeline."""

    def __init__(self):
        self.dir_base = _dir_reportes()

    def _dir_hoy(self) -> Path:
        hoy = date.today().isoformat()
        d = self.dir_base / hoy
        d.mkdir(parents=True, exist_ok=True)
        return d

    # ------------------------------------------------------------------
    # Archivo 00: Resumen ejecutivo (lectura rápida, ≤1 página)
    # ------------------------------------------------------------------
    def _escribir_resumen(self, resultado, dir_hoy: Path) -> Path:
        from src.analyzer.claude_analyzer import AnalisisResult
        r: AnalisisResult = resultado
        top3 = r.temas[:3]
        lineas = [
            f"# Resumen político del día — {r.fecha}",
            "",
            f"> {r.narrativa_general}",
            "",
            "## Top 3 temas del día",
            "",
        ]
        for i, t in enumerate(top3, 1):
            estrellas = "⭐" * min(t.relevancia, 5) if t.relevancia else ""
            lineas += [
                f"### {i}. {t.titulo} {estrellas}",
                f"**Categoría:** {t.categoria}  ",
                f"**Relevancia:** {t.relevancia}/10",
                "",
                t.resumen,
                "",
            ]
        lineas += [
            "---",
            "",
            "## Informes detallados",
            "",
            "| Archivo | Contenido |",
            "|---|---|",
            "| [01_tendencias.md](01_tendencias.md) | Ranking completo de tendencias |",
            "| [02_analisis.md](02_analisis.md) | Análisis profundo por tema |",
            "| [03_posts_redes.md](03_posts_redes.md) | Borradores de posts |",
            "| [04_fuentes.md](04_fuentes.md) | Fuentes y datos crudos |",
        ]
        path = dir_hoy / "00_resumen.md"
        path.write_text("\n".join(lineas), encoding="utf-8")
        return path

    # ------------------------------------------------------------------
    # Archivo 01: Tendencias rankeadas
    # ------------------------------------------------------------------
    def _escribir_tendencias(self, resultado, dir_hoy: Path) -> Path:
        from src.analyzer.claude_analyzer import AnalisisResult
        r: AnalisisResult = resultado
        lineas = [
            f"# Tendencias políticas rankeadas — {r.fecha}",
            "",
            f"**Total de temas identificados:** {len(r.temas)}",
            "",
            "| # | Tema | Categoría | Relevancia | Actores clave |",
            "|---|---|---|---|---|",
        ]
        for i, t in enumerate(r.temas, 1):
            actores = ", ".join(t.actores[:3]) if t.actores else "—"
            barra = "█" * t.relevancia + "░" * (10 - t.relevancia)
            lineas.append(
                f"| {i} | **{t.titulo}** | {t.categoria} | {barra} {t.relevancia}/10 | {actores} |"
            )
        lineas += ["", "---", ""]
        for i, t in enumerate(r.temas, 1):
            lineas += [
                f"## {i}. {t.titulo}",
                "",
                f"**Relevancia:** {t.relevancia}/10 | **Categoría:** {t.categoria}",
                "",
                f"**Resumen:** {t.resumen}",
                "",
                f"**Actores:** {', '.join(t.actores) if t.actores else 'No identificados'}",
                "",
                f"**Fuentes:** {', '.join(t.fuentes_relacionadas) if t.fuentes_relacionadas else '—'}",
                "",
            ]
        path = dir_hoy / "01_tendencias.md"
        path.write_text("\n".join(lineas), encoding="utf-8")
        return path

    # ------------------------------------------------------------------
    # Archivo 02: Análisis en profundidad
    # ------------------------------------------------------------------
    def _escribir_analisis(self, resultado, dir_hoy: Path) -> Path:
        from src.analyzer.claude_analyzer import AnalisisResult
        r: AnalisisResult = resultado
        lineas = [
            f"# Análisis político en profundidad — {r.fecha}",
            "",
            "## Panorama general",
            "",
            r.narrativa_general,
            "",
            "## Recomendaciones para comunicadores",
            "",
            r.recomendaciones,
            "",
            "---",
            "",
            "## Análisis por tema",
            "",
        ]
        for i, t in enumerate(r.temas, 1):
            lineas += [
                f"### {i}. {t.titulo}",
                "",
                f"**Relevancia:** {t.relevancia}/10  ",
                f"**Categoría:** {t.categoria}",
                "",
                "#### Resumen",
                t.resumen,
                "",
                "#### Contexto y antecedentes",
                t.contexto,
                "",
                "#### Actores involucrados",
                "\n".join(f"- {a}" for a in t.actores) if t.actores else "- No identificados",
                "",
                "---",
                "",
            ]
        path = dir_hoy / "02_analisis.md"
        path.write_text("\n".join(lineas), encoding="utf-8")
        return path

    # ------------------------------------------------------------------
    # Archivo 03: Posts de redes sociales
    # ------------------------------------------------------------------
    def _escribir_posts(self, resultado, dir_hoy: Path) -> Path:
        from src.analyzer.claude_analyzer import AnalisisResult
        r: AnalisisResult = resultado
        lineas = [
            f"# Borradores de posts para redes sociales — {r.fecha}",
            "",
            "> Usa estos borradores como punto de partida. Revisa y personaliza antes de publicar.",
            "",
        ]
        if not r.posts:
            lineas.append("_No se generaron posts en esta ejecución._")
        else:
            for titulo_tema, plataformas in r.posts.items():
                lineas += [
                    f"## Tema: {titulo_tema}",
                    "",
                ]
                # X/Twitter
                tw = plataformas.get("X_Twitter", {})
                if tw:
                    lineas += [
                        "### X (Twitter)",
                        "```",
                        tw.get("texto", ""),
                        "```",
                        f"**Hashtags:** {' '.join(tw.get('hashtags', []))}",
                        "",
                    ]
                # Instagram
                ig = plataformas.get("Instagram", {})
                if ig:
                    lineas += [
                        "### Instagram",
                        "```",
                        ig.get("caption", ""),
                        "```",
                        f"**Hashtags:** {' '.join(ig.get('hashtags', []))}",
                        "",
                    ]
                # Facebook
                fb = plataformas.get("Facebook", {})
                if fb:
                    lineas += [
                        "### Facebook",
                        "```",
                        fb.get("texto", ""),
                        "```",
                        "",
                    ]
                # TikTok
                tt = plataformas.get("TikTok", {})
                if tt:
                    lineas += [
                        "### TikTok — Guión de video",
                        "```",
                        tt.get("guion", ""),
                        "```",
                        f"**Descripción:** {tt.get('descripcion', '')}",
                        "",
                    ]
                lineas.append("---")
                lineas.append("")
        path = dir_hoy / "03_posts_redes.md"
        path.write_text("\n".join(lineas), encoding="utf-8")
        return path

    # ------------------------------------------------------------------
    # Archivo 04: Fuentes y datos crudos
    # ------------------------------------------------------------------
    def _escribir_fuentes(self, datos_raw: list[dict], resultado, dir_hoy: Path) -> Path:
        from src.analyzer.claude_analyzer import AnalisisResult
        r: AnalisisResult = resultado
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lineas = [
            f"# Fuentes de datos — {r.fecha}",
            "",
            f"**Generado:** {ts}  ",
            f"**Total de items recolectados:** {len(datos_raw)}",
            "",
        ]

        # Google Trends
        trends = [d for d in datos_raw if "google_trends" in d.get("source", "")]
        if trends:
            lineas += [
                f"## Google Trends ({len(trends)} items)",
                "",
                "| Keyword | Score | Fuente |",
                "|---|---|---|",
            ]
            for t in trends:
                score = t.get("score") or "—"
                lineas.append(f"| {t['keyword']} | {score} | {t['source']} |")
            lineas.append("")

        # RSS
        rss = [d for d in datos_raw if d.get("source") == "rss"]
        if rss:
            lineas += [
                f"## Artículos RSS ({len(rss)} artículos)",
                "",
                "| Fuente | Título | Fecha | URL |",
                "|---|---|---|---|",
            ]
            for art in rss:
                fecha = (art.get("fecha") or "")[:10]
                url = art.get("url", "")
                titulo = art["titulo"].replace("|", "\\|")[:80]
                lineas.append(f"| {art['fuente']} | {titulo} | {fecha} | {url} |")
            lineas.append("")

        # Twitter
        twitter = [d for d in datos_raw if d.get("source") == "twitter"]
        if twitter:
            lineas += [
                f"## Twitter/X ({len(twitter)} tweets)",
                "",
            ]
            for tw in twitter:
                lineas.append(
                    f"- **@{tw.get('usuario', '?')}** ({tw.get('likes', 0)} likes): "
                    f"{tw.get('texto', '')[:150]}"
                )
            lineas.append("")

        # TikTok
        tiktok = [d for d in datos_raw if d.get("source") == "tiktok"]
        if tiktok:
            lineas += [
                f"## TikTok ({len(tiktok)} videos)",
                "",
            ]
            for tt in tiktok:
                lineas.append(
                    f"- **#{tt.get('hashtag', '')}** | {tt.get('vistas', 0):,} vistas: "
                    f"{tt.get('descripcion', '')[:100]}"
                )

        path = dir_hoy / "04_fuentes.md"
        path.write_text("\n".join(lineas), encoding="utf-8")
        return path

    # ------------------------------------------------------------------
    # Índice general de reportes
    # ------------------------------------------------------------------
    def _actualizar_indice(self) -> None:
        """Actualiza reports/README.md con la lista de todos los reportes."""
        reportes = sorted(
            [d for d in self.dir_base.iterdir() if d.is_dir()],
            reverse=True,
        )
        lineas = [
            "# Índice de informes — Trends-Política",
            "",
            "| Fecha | Resumen | Tendencias | Análisis | Posts | Fuentes |",
            "|---|---|---|---|---|---|",
        ]
        for r in reportes:
            fecha = r.name
            def link(nombre: str) -> str:
                p = r / nombre
                return f"[ver]({fecha}/{nombre})" if p.exists() else "—"
            lineas.append(
                f"| {fecha} | {link('00_resumen.md')} | {link('01_tendencias.md')} | "
                f"{link('02_analisis.md')} | {link('03_posts_redes.md')} | {link('04_fuentes.md')} |"
            )
        (self.dir_base / "README.md").write_text("\n".join(lineas), encoding="utf-8")

    # ------------------------------------------------------------------
    # Método principal
    # ------------------------------------------------------------------
    def generar(self, resultado, datos_raw: list[dict]) -> dict[str, Path]:
        """
        Genera los 5 archivos MD del informe y actualiza el índice.
        Retorna un dict con los paths de los archivos generados.
        """
        dir_hoy = self._dir_hoy()
        archivos = {
            "resumen": self._escribir_resumen(resultado, dir_hoy),
            "tendencias": self._escribir_tendencias(resultado, dir_hoy),
            "analisis": self._escribir_analisis(resultado, dir_hoy),
            "posts": self._escribir_posts(resultado, dir_hoy),
            "fuentes": self._escribir_fuentes(datos_raw, resultado, dir_hoy),
        }
        self._actualizar_indice()
        logger.info("Informe generado en: %s", dir_hoy)
        return archivos
