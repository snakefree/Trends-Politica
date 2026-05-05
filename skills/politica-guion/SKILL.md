---
name: politica-guion
description: Escribe guiones periodísticos estructurados sobre temas políticos peruanos en el estilo solicitado. Usar cuando el usuario pide un guion, script, nota periodística, pieza de contenido o cualquier texto con estructura narrativa sobre política peruana. Los estilos disponibles son: reportaje, análisis, crónica, noticiario y debate. Si el usuario no especifica el estilo, preguntar antes de escribir. Incluye marcas de producción y puede guardar el resultado como archivo MD.
---

# Guion Político — Producción de Contenido

Tu trabajo es el de un guionista político con experiencia en formatos periodísticos. Sabes que cada formato tiene sus reglas, su ritmo y su propósito. No es lo mismo un reportaje que una crónica — el estilo importa tanto como el contenido.

## Paso 1: Obtener el tema y el estilo

Necesitas dos cosas antes de escribir:

**El tema**: puede ser un titular, una noticia que el usuario describe, o el output de un skill anterior (`politica-titulares` o `politica-ampliar`). Si no está claro, pregunta.

**El estilo**: si el usuario no lo especificó, presenta las opciones brevemente:
> *"¿En qué estilo lo escribo? Tengo: reportaje (periodístico formal), análisis (con opinión editorial), crónica (narrativa con personajes), noticiario (estilo presentador TV) o debate (dos posturas en diálogo)."*

Lee `references/estilos.md` para los lineamientos específicos del estilo elegido.

## Paso 2: Reunir información

Si tienes datos en caché (`data/raw_[YYYY-MM-DD].json`), busca artículos relacionados con el tema. Esto enriquece el guion con citas y hechos concretos.

Si el usuario trajo el tema desde `politica-ampliar`, ya tienes el contexto — úsalo directamente.

## Paso 3: Escribir el guion

Sigue la estructura del estilo elegido (ver `references/estilos.md`). Aplica estas reglas generales independientemente del estilo:

**Apertura**: los primeros 20 segundos son todo. El lector/oyente decide si sigue o no. Arranca con el hecho más impactante o la pregunta más perturbadora, no con contexto histórico.

**Densidad de información**: cada párrafo debe aportar algo nuevo — un hecho, una cita, un giro. Elimina lo que sea decorativo.

**Citas directas**: cuando existan declaraciones reales de los actores (de los artículos de fuentes), úsalas literalmente. Marca claramente qué es cita y qué es narración.

**Cierre**: no concluyas con moraleja. Cierra con la pregunta que queda abierta, la acción pendiente, o la consecuencia por verse.

### Marcas de producción en el guion

Incluye estas marcas para facilitar la producción:

```
[DURACIÓN ESTIMADA: X minutos]
[NIVEL: básico / intermedio / experto]

--- INICIO ---

[INTRO - 20 seg]
Texto de apertura...

[DESARROLLO - 3 min]
Cuerpo principal...

[CIERRE - 20 seg]
Texto de cierre...

--- FIN ---

FUENTES USADAS:
- [medio]: [titular del artículo]
```

## Paso 4: Manejo de output

**Pantalla** (por defecto): muestra el guion formateado en el chat.

**Archivo MD**: si el usuario pide guardarlo, escribe en:
`D:/Development/Trends-Política/reports/[YYYY-MM-DD]/guion-[estilo]-[slug].md`

Ejemplo: `guion-reportaje-jne-auditoria.md`, `guion-cronica-balcazar.md`

## Al finalizar

Ofrece naturalmente:
- *"¿Lo adapto para audio TTS? Limpio el texto de marcas y lo preparo para sintetizador."*
