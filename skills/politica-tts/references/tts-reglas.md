# Reglas de Escritura para TTS — Política Peruana

Estas reglas existen porque los sintetizadores de voz leen literalmente. Un símbolo fuera de lugar, un acrónimo sin expandir o una oración demasiado larga puede arruinar el audio. Aplica todas las reglas siempre.

---

## 1. Eliminar markdown y caracteres especiales

**Prohibido en el texto TTS:**
- `#`, `##`, `###` (encabezados)
- `**negrita**`, `*cursiva*`
- `- ` o `* ` (listas con viñetas)
- `|` (tablas)
- `[texto](url)` (enlaces)
- Emojis de cualquier tipo (🌶️, ⭐, etc.)
- Guiones largos `—` → reemplazar por coma o punto
- Comillas tipográficas `"..."` → reemplazar por comillas simples `'...'` o eliminar

**Permitido:**
- Punto, coma, punto y coma, dos puntos
- Paréntesis para aclaraciones
- Mayúsculas para énfasis de siglas (solo la primera vez)
- Puntos suspensivos `...` como pausa larga

---

## 2. Expandir siglas y acrónimos

La primera vez que aparece una sigla, escríbela completa. Después puedes usar la sigla sola.

| Sigla | Expansión |
|-------|-----------|
| JNE | Jurado Nacional de Elecciones |
| ONPE | Oficina Nacional de Procesos Electorales |
| JNJ | Junta Nacional de Justicia |
| PNP | Policía Nacional del Perú |
| PCM | Presidencia del Consejo de Ministros |
| MEF | Ministerio de Economía y Finanzas |
| MTC | Ministerio de Transportes y Comunicaciones |
| Minedu | Ministerio de Educación |
| SUNAT | Superintendencia Nacional de Aduanas y de Administración Tributaria |
| FF.AA. | Fuerzas Armadas |
| PJ | Poder Judicial |
| TC | Tribunal Constitucional |

**Regla general:** si dudas, expándelo. Es mejor escuchar la versión larga una vez que confundir al oyente.

---

## 3. Números en palabras

Todos los números se escriben en palabras. Las cantidades grandes se redondean a la expresión más natural.

| Texto original | Texto TTS |
|---------------|-----------|
| 26,000 votos | veintiséis mil votos |
| S/31 millones | treinta y un millones de soles |
| 97.78% | noventa y siete punto setenta y ocho por ciento |
| 15 meses | quince meses |
| 2026 | dos mil veintiséis |
| 4 de mayo | cuatro de mayo |
| 08:00 | las ocho de la mañana |
| F-16 | aviones F dieciséis |

**Excepción:** artículos de ley o decreto con número (ej: "Ley 30057") → leer como "Ley treinta mil cincuenta y siete".

---

## 4. Pronunciación de nombres y términos complejos

Cuando un nombre puede pronunciarse mal o de forma ambigua, agrega la pronunciación entre paréntesis la primera vez:

- Boluarte → **Boluarte (Bo-LUAR-te)**
- Nicanor Boluarte → **Nicanor Boluarte (Ni-ca-NOR Bo-LUAR-te)**
- Colcabamba → **Colcabamba (Col-ca-BAM-ba)**
- Antauro → **Antauro (An-TAU-ro)**
- Keiko → se pronuncia naturalmente, no necesita ayuda
- Petroperú → **Petro-Perú** (con guion para que el sintetizador no lo fusione)

Nombres de distritos o localidades poco conocidas: incluir siempre pronunciación aproximada.

---

## 5. Estructura de oraciones para audio

**Oraciones cortas.** El límite de comodidad auditiva es ~20 palabras. Divide las oraciones largas.

**Incorrecto:**
> *El ministro Balcázar, quien había sido nombrado en el cargo hace tres meses, aseguró en una conferencia de prensa realizada el lunes por la mañana que la compra de los aviones F-16, que según él se hizo de manera secreta y sin su conocimiento, pone en riesgo la seguridad nacional.*

**Correcto:**
> *El ministro Balcázar hizo una revelación el lunes por la mañana. Dijo que la compra de los aviones F dieciséis se hizo en secreto. Y afirmó que él no tuvo conocimiento del proceso.*

**Sin subordinadas encadenadas.** Cada cláusula subordinada que se agrega es un riesgo de que el oyente pierda el hilo.

---

## 6. Marcadores de pausa

Usa puntuación estándar para controlar el ritmo. Los sintetizadores modernos respetan la puntuación:

| Pausa deseada | Cómo escribirlo |
|--------------|----------------|
| Pausa breve | coma `,` |
| Pausa media | punto y coma `;` o dos puntos `:` |
| Pausa larga | punto `.` |
| Pausa dramática | puntos suspensivos `...` |
| Pausa antes de lista | dos puntos `:` |

Para sintetizadores que soportan SSML (como Google TTS o Azure), puedes agregar al final del archivo una nota como: `[Nota SSML: agregar <break time="1s"/> después de cada encabezado]`

---

## 7. Cálculo de duración

**Velocidad de referencia:** 130 palabras por minuto (ritmo conversacional natural).

Fórmulas:
- **Palabras totales / 130 = minutos**
- Redondear al 15 segundos más cercano

Ejemplos:
- 130 palabras → 1 minuto
- 260 palabras → 2 minutos
- 390 palabras → 3 minutos
- 650 palabras → 5 minutos

Siempre incluir al final del texto TTS:
```
[Total: N palabras — Duración estimada: X min Y seg a 130 ppm]
```

---

## 8. Tratamiento de citas directas

Las citas de funcionarios o políticos son frecuentes. Para TTS:

**Sin comillas tipográficas:**
> *El ministro dijo, y cito textualmente: el proceso fue absolutamente transparente, fin de la cita.*

O más natural:
> *En sus propias palabras, el ministro afirmó que el proceso fue absolutamente transparente.*

Si la cita es larga (+20 palabras), parafrasear es mejor que citar textual. El oído no puede releer.

---

## 9. Checklist final antes de entregar

Antes de dar el texto por listo, verifica:

- [ ] Sin markdown ni caracteres especiales
- [ ] Todas las siglas expandidas al menos una vez
- [ ] Todos los números en palabras
- [ ] Pronunciaciones difíciles marcadas
- [ ] Oraciones de máximo 20 palabras
- [ ] Citas sin comillas tipográficas
- [ ] Duración calculada al final
