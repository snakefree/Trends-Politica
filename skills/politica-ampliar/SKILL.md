---
name: politica-ampliar
description: Amplía y desarrolla un titular o tema político peruano específico en un análisis informativo de 400-600 palabras con contexto, actores y perspectivas. Usar cuando el usuario pide más información sobre una noticia concreta, quiere saber qué hay detrás de un tema, pide "ampliame esto", "cuéntame más sobre X", "desarrolla el tema de X", o hace preguntas de profundización sobre cualquier asunto político peruano mencionado. Busca en los datos recolectados todos los artículos relacionados antes de responder.
---

# Ampliar un Titular Político

Tu trabajo es el de un corresponsal político que tiene acceso a múltiples fuentes y puede armar un cuadro completo de una situación. No te limitas al titular — buscas el contexto, los actores, las implicaciones.

## Paso 1: Identificar el tema a ampliar

El usuario puede indicarlo de varias formas:
- Citando un titular exacto: *"ampliame el del JNE y la auditoría"*
- Describiendo el tema: *"lo de Balcázar y los aviones"*
- Referenciando posición: *"el primero de la lista"* (si acaba de ver titulares)

Si no queda claro, pregunta con una sola línea: *"¿De qué titular o tema quieres más detalle?"*

## Paso 2: Buscar artículos relacionados

Lee el archivo de caché del día: `D:/Development/Trends-Política/data/raw_[YYYY-MM-DD].json`

Usa la fecha de hoy. Si el archivo no existe, llama primero a `obtener_tendencias` (MCP).

Busca **todos** los artículos que mencionen el tema en su `titulo` o `resumen`. Un tema puede aparecer con nombres distintos en cada medio (ej: "Balcázar" puede aparecer como "ministro de Defensa" o "el caso de los F-16").

## Paso 3: Construir la ampliación

Genera una pieza informativa con estas secciones. Adapta el nivel de detalle según la información disponible — no rellenes con suposiciones.

### Estructura

**[Titular descriptivo del tema — no el mismo que el artículo original]**

**Qué pasó**
Los hechos concretos en orden cronológico. Qué se dijo, quién lo dijo, cuándo ocurrió. Sin opinión todavía.

**Quiénes están involucrados**
Lista los actores principales con una línea sobre su rol en esta historia:
- *[Actor]:* [qué papel juega en este asunto]

**Por qué importa**
Contexto: ¿esto es nuevo o tiene antecedentes? ¿Qué principio institucional o político está en juego? ¿Qué grupos o ciudadanos se ven afectados?

**Qué sigue**
Posibles desarrollos: ¿hay plazos, votaciones, audiencias pendientes? ¿Qué tienen que decir los actores? Presenta esto como posibilidades, no certezas.

**Fuentes consultadas**
Lista los artículos usados: `[Nombre del medio]: [título del artículo]`

### Extensión objetivo
400-600 palabras. Suficiente para entender bien el tema; no tanto como para aburrir.

## Paso 4: Manejo de output

**Pantalla** (por defecto): muestra la ampliación formateada en el chat.

**Archivo MD**: si el usuario pide guardarlo, escribe en:
`D:/Development/Trends-Política/reports/[YYYY-MM-DD]/ampliacion-[slug-del-tema].md`

El slug es el tema en minúsculas con guiones: "balcazar-f16", "jne-auditoria", "masacre-colcabamba".

Usa el tool `Write` para escribir el archivo.

## Al finalizar

Ofrece las siguientes acciones naturalmente (sin ser insistente):
- *"¿Quieres un guion sobre esto? Puedo hacerlo en estilo reportaje, análisis o crónica."*
- *"¿Lo preparo para audio TTS?"*
