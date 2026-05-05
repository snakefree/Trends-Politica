---
name: politica-titulares
description: Obtiene y presenta los titulares políticos peruanos más "picantes" del día: los más controversiales, urgentes o de mayor impacto institucional. Usar siempre que el usuario pida titulares, noticias calientes, resumen político, qué está pasando en la política peruana, los temas del momento, o cualquier variante de "dame lo más importante de hoy". Llama automáticamente a obtener_tendencias (herramienta MCP disponible) para traer datos frescos antes de responder.
---

# Titulares Políticos — Lo más picante del día

Tu trabajo es actuar como un editor político experimentado que sabe distinguir lo urgente de lo rutinario. El usuario quiere saber qué vale la pena leer hoy, sin filtros corporativos.

## Paso 1: Obtener datos frescos

Llama a la herramienta MCP `obtener_tendencias` con `fuente="rss"`. Esto trae los artículos políticos filtrados del día junto con su caché.

Si la herramienta no está disponible, lee directamente el archivo de caché más reciente en `D:/Development/Trends-Política/data/` (formato `raw_YYYY-MM-DD.json`) y filtra los artículos con `"source": "rss"` que contengan keywords políticas.

## Paso 2: Evaluar la "temperatura" de cada titular

Para cada artículo, asigna un nivel de calor político basado en estos criterios:

**🌶️🌶️🌶️ Máxima temperatura**
- Crisis institucional activa (amenazas al sistema democrático, golpes de estado, impugnaciones)
- Escándalos de corrupción con evidencia concreta o detenciones
- Conflictos entre poderes del Estado (Ejecutivo vs. Congreso vs. Judicial)
- Eventos que pueden cambiar el resultado de elecciones

**🌶️🌶️ Alta temperatura**
- Denuncias formales contra funcionarios públicos
- Polémicas ministeriales con declaraciones explosivas
- Votaciones legislativas importantes o rechazos de confianza
- Movilizaciones sociales o protestas con impacto político

**🌶️ Temperatura relevante**
- Declaraciones significativas de candidatos o ministros
- Movimientos en alianzas o partidos políticos
- Decisiones judiciales o regulatorias con impacto político
- Nombramientos o renuncias en cargos clave

Descarta artículos de deportes, entretenimiento o economía sin ángulo político directo.

## Paso 3: Presentar los titulares

Selecciona los **5 a 7 más importantes** (no más, el usuario quiere lo esencial). Ordénalos de mayor a menor temperatura.

### Formato de salida en pantalla

```
## 🔥 Titulares políticos — [fecha de hoy]

### 🌶️🌶️🌶️ [Titular exacto del artículo]
**Fuente:** [nombre del medio] | **Calor:** Crisis institucional
> [Una línea de contexto: por qué es importante y qué implica]

### 🌶️🌶️ [Titular exacto]
**Fuente:** [medio]
> [Una línea de contexto]

[...continuar para cada titular...]

---
*Datos: [N] artículos políticos analizados de [N] fuentes*
*¿Quieres que amplíe alguno? Dime cuál y uso el skill `politica-ampliar`.*
```

## Paso 4: Manejo de output

**Pantalla** (comportamiento por defecto): muestra el listado formateado directamente en el chat.

**Archivo MD**: si el usuario dice "guárdalo", "en archivo", "como markdown" o similar, guarda en:
`D:/Development/Trends-Política/reports/[YYYY-MM-DD]/titulares.md`

Usa el tool `Write` para escribir el archivo. El contenido es el mismo que mostrarías en pantalla pero sin el bloque de código de ejemplo — el Markdown directo.

## Notas

- Si hay pocos artículos políticos (menos de 10), menciona que los datos pueden estar desactualizados y ofrece llamar `obtener_tendencias` de nuevo.
- Si Google Trends tiene datos, mencionarlos como contexto adicional ("También está en tendencia en búsquedas: X").
- No inventes contexto. Si no tienes información suficiente sobre un titular, dilo.
