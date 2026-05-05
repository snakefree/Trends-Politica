---
name: politica-tts
description: Convierte contenido político peruano en texto optimizado para síntesis de voz (TTS/text-to-speech). Usar cuando el usuario pide preparar texto para audio, narración en voz alta, script para sintetizador, guion TTS, o cualquier variante de "quiero que esto se pueda leer con voz sintética". También usar cuando el usuario pide duración estimada de un audio o quiere un texto sin caracteres especiales para locutor. Lee las reglas de tts-reglas.md antes de escribir.
---

# Guion para Texto a Voz (TTS)

El texto escrito y el texto hablado son géneros distintos. Lo que funciona en pantalla puede sonar torpe o confuso cuando una máquina lo lee en voz alta. Tu trabajo es hacer la traducción.

## Paso 1: Obtener el contenido base

El contenido puede venir de:
- **Skill anterior**: output de `politica-ampliar` o `politica-guion` en esta misma conversación
- **Tema directo**: el usuario describe lo que quiere narrar
- **Titular específico**: el usuario señala una noticia del día

Si el usuario trae contenido existente, úsalo como base y adáptalo. Si trae solo un tema, genera el contenido tú mismo siguiendo las reglas TTS desde el principio.

## Paso 2: Leer las reglas TTS

Lee `references/tts-reglas.md` antes de escribir. Esas reglas son el core del skill — no las saltes.

## Paso 3: Escribir el texto TTS

El texto resultante debe poder pegarse directamente en cualquier sintetizador de voz (ElevenLabs, Google TTS, Azure, etc.) y sonar natural sin edición adicional.

### Estructura del output

```
[GUION TTS — FECHA]
[Duración estimada: X minutos Y segundos]
[Velocidad base: 130 palabras por minuto]

---

[Texto completo aquí, limpio, sin markdown]

---

[Total de palabras: N]
```

El texto entre los separadores `---` es lo que se pega en el sintetizador. Todo lo demás es metadata para el usuario.

## Paso 4: Manejo de output

**Pantalla** (por defecto): muestra el guion TTS completo en el chat. El texto limpio va en un bloque de código para facilitar el copiado:

````
```
[Texto TTS limpio aquí]
```
````

**Archivo MD**: si el usuario pide guardarlo, escribe en:
`D:/Development/Trends-Política/reports/[YYYY-MM-DD]/tts-[slug].md`

El archivo incluye el texto TTS en un bloque de código y la metadata de duración.

## Al finalizar

Si el usuario tiene un sintetizador específico (ElevenLabs, Google, Azure, local), ofrece ajustar el texto para ese motor si hay diferencias relevantes en cómo maneja pausas o pronunciación.
