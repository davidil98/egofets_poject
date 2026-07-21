# Teoría: Saturación y extracción de $V_{th}$ por $\sqrt{I_{DS}}$

Notas conceptuales para entender qué estás midiendo y por qué se hace así en
el análisis de curvas transfer de EGOFETs.

Contexto: dispositivo tipo p (los huecos son los portadores mayoritarios),
$I_{DS}$ se mide negativo, $V_{th}$ es negativo.

---

## 1. ¿Qué es la "saturación" en un transistor de efecto de campo?

En cualquier FET (Si-MOSFET, OFET, EGOFET) hay **dos regímenes de operación**
definidos por la relación entre $V_{DS}$ y $(V_{GS} - V_{th})$:

| Régimen | Condición | Comportamiento de $I_{DS}$ |
|---|---|---|
| **Lineal (triodo)** | $\vert V_{DS} \vert \ll \vert V_{GS} - V_{th} \vert$ | Crece linealmente con $V_{DS}$ |
| **Saturación** | $\vert V_{DS} \vert \geq \vert V_{GS} - V_{th} \vert$ | Se "aplana", ya no depende de $V_{DS}$ |

Físicamente, en saturación el canal se **"pincha"** (pinch-off) cerca del
drenador: por mucho que aumentes $V_{DS}$, la corriente no sube más (o sube
muy poco). En la curva $I_{DS}$–$V_{DS}$ (output curve) lo ves como una zona
plana después de la rodilla.

La ecuación cuadrática que rige la zona de saturación es la clave para el
método $\sqrt{I_{DS}}$:

$$I_{DS}^{sat} = \frac{1}{2} \mu C \frac{W}{L} (V_{GS} - V_{th})^2$$

**Nota para EGOFETs:** esta es la fórmula del MOSFET/OFET clásico. En un
EGOFET la "dieléctrico" es un electrolito y la operación puede tener
componente electroquímica (los iones penetran el semiconductor), así que la
ley cuadrática no siempre se cumple limpia. Es algo que hay que **verificar
en los datos**.

### Relación con la curva transfer

La curva transfer es $I_{DS}$ vs $V_{GS}$ a $V_{DS}$ **fija**. Si esa $V_{DS}$
está elegida para que el transistor opere en saturación (típicamente
$V_{DS} \geq V_{GS} - V_{th}$), entonces toda la curva transfer está en el
régimen de saturación, y se cumple la relación cuadrática.

Visualmente en la transfer curve:

- **Off state**: $V_{GS} < V_{th}$, $I_{DS} \approx 0$ (corriente de fuga)
- **Subthreshold**: zona de transición exponencial (sirve para extraer $SS$)
- **On state**: $V_{GS} > V_{th}$, $I_{DS}$ sube

---

## 2. El método $\sqrt{I_{DS}}$ para extraer $V_{th}$

La idea es brillante por su simplicidad: si en saturación
$I_{DS} \propto (V_{GS} - V_{th})^2$, entonces tomando raíz cuadrada se obtiene
una relación **lineal** en $V_{GS}$. Graficando $\sqrt{I_{DS}}$ vs $V_{GS}$ en
la región de saturación, sale una recta, y la intersección con el eje $V_{GS}$
(donde $\sqrt{I_{DS}} = 0$) es exactamente $V_{th}$.

### Procedimiento

1. Identificar qué $V_{DS}$ de las curvas transfer satura el dispositivo
   (la más alta que tengas).
2. Tomar **solo los datos del forward sweep** (no el reverse, para evitar
   histéresis, ver sección 4).
3. En esa curva, restringir a la región **on** (donde ya pasó el threshold):
   esa es la zona lineal en el plot $\sqrt{I_{DS}}$–$V_{GS}$.
4. Ajustar una recta (regresión lineal) y leer el intercepto.

### Trampas típicas en EGOFETs

- **Que no haya verdadera saturación**: la "transfer" a $V_{DS}$ baja puede
  no entrar nunca en pinch-off. Revisar la output curve correspondiente.
- **Que la ley cuadrática falle**: la zona lineal en $\sqrt{I_{DS}}$ puede ser
  corta o estar curvada. Ahí el $V_{th}$ extraído depende mucho de dónde
  elijas la ventana de ajuste (de ahí la nota de la notebook sobre
  `vgs_range`).

---

## 3. ¿Por qué elegir el $V_{DS}$ más alto?

**Intuición:** la "saturación" no es una propiedad del dispositivo, es una
**condición de operación** que depende de cuánto $V_{DS}$ aplicas. Es como
una bañera: el agua (corriente) se desborda (satura) solo si el grifo
($V_{DS}$) está suficientemente abierto en relación al desagüe
($V_{GS} - V_{th}$).

**Formalmente**, la condición de saturación es:

$$|V_{DS}| \geq |V_{GS} - V_{th}|$$

Si esta condición se cumple, la ley cuadrática (la que usa el método
$\sqrt{I_{DS}}$) es válida. Si no se cumple, estás en régimen lineal y la
fórmula no aplica.

**¿Por qué el $V_{DS}$ más alto te da más garantías?**

- A $V_{DS}$ bajo, la condición solo se cumple para $V_{GS}$ muy cerca de
  $V_{th}$. Para el resto del barrido, el dispositivo está en lineal y el
  método $\sqrt{I_{DS}}$ falla.
- A $V_{DS}$ alto, la condición se cumple para **todo** el rango de $V_{GS}$
  que se va a usar en el ajuste. Toda la curva está en saturación.

**La prueba definitiva** no es el $V_{DS}$ elegido, sino mirar la **output
curve** ($I_{DS}$ vs $V_{DS}$) del mismo dispositivo. Si en algún $V_{GS}$ ves
una zona plana (corriente que ya no sube con $V_{DS}$), el dispositivo está
saturando ahí. Eso se hace en la notebook 03. Mientras tanto, usar la $V_{DS}$
más alta es la apuesta más segura.

---

## 4. ¿Por qué separar forward de reverse?

**Intuición:** un EGOFET tiene iones en el electrolito que se mueven
lentamente. Cuando barres $V_{GS}$ de un extremo a otro y luego vuelves, los
iones no alcanzan a redistribuirse al mismo ritmo: la curva "ida" y la curva
"vuelta" no coinciden. Esto es la **histéresis**.

**¿Por qué es un problema para el método $\sqrt{I_{DS}}$?**

La ley cuadrática asume que el dispositivo está en un **estado
cuasi-estático**: que la carga en el canal responde instantáneamente a
$V_{GS}$. En un EGOFET eso no se cumple del todo, y la histéresis es la
manifestación de esa lentitud. Si se mezclan forward y reverse, se están
promediando dos estados físicos diferentes del dispositivo, y la curva
resultante no satisface la ley cuadrática limpia. Cualquier ajuste que se
haga va a dar un número sin significado físico claro.

**¿Qué se hace en la práctica?**

- Lo estándar es extraer $V_{th}$ del **forward sweep** y reportar la
  histéresis por separado como
  $\Delta V_{th} = V_{th}^{rev} - V_{th}^{fwd}$. La histéresis es en sí misma
  un parámetro del dispositivo (dice qué tan "rápido" responde, o qué tan
  "limpio" es el apilado semiconductor/electrolito).
- En la notebook eventualmente se tendrán dos $V_{th}$ por medición: uno por
  dirección, más el $\Delta V_{th}$.

---

## 5. ¿Qué significa matemáticamente la raíz y el valor absoluto?

Esta es la parte más conceptual, porque es un truco de **linealización** muy
común en física.

**El punto de partida**, para un EGOFET tipo p en saturación:

$$|I_{DS}| = \frac{1}{2}\mu C \frac{W}{L}(V_{GS} - V_{th})^2$$

Nota: la magnitud, no la corriente con signo. Esto se cumple para $V_{GS}$
del lado del encendido ($V_{GS} > V_{th}$ en tipo p, donde $V_{th}$ es
negativo).

**Tomando raíz cuadrada de ambos lados:**

$$\sqrt{|I_{DS}|} = \sqrt{\frac{1}{2}\mu C \frac{W}{L}} \cdot |V_{GS} - V_{th}|$$

Y como se está en la región de encendido, $|V_{GS} - V_{th}| = V_{GS} - V_{th}$:

$$\sqrt{|I_{DS}|} = \underbrace{\sqrt{\frac{1}{2}\mu C \frac{W}{L}}}_{m} \cdot (V_{GS} - \underbrace{V_{th}}_{b})$$

¡Esto es una **recta**! Con:

- **pendiente** $m = \sqrt{\frac{1}{2}\mu C \frac{W}{L}}$ → relacionado con
  la movilidad.
- **intercepto en el eje x** en $V_{GS} = V_{th}$ (porque ahí
  $\sqrt{|I_{DS}|} = 0$).

### ¿Por qué funciona este truco?

Se tiene una parábola $y = m^2(x-b)^2$. Su raíz $\sqrt{y} = m|x-b|$ es una
"V" con el vértice en $x=b$. En la región de encendido (una de las ramas de
la V), eso es una recta. Gráficamente:

```
  y (parábola)              √y (línea)
     |   *                       |
     |  * *                      |        *
     | *   *                     |      *
     |*     *                    |    *
     *-------*--- x              *---*-------- x
             b                          b
```

### ¿Por qué el valor absoluto en $I_{DS}$?

Raíz de un número negativo es imaginaria. En un EGOFET tipo p $|I_{DS}|$ es
del orden de $10^{-9}$ a $10^{-10}$ A, pero **negativo**. Sin el valor
absoluto, $\sqrt{-10^{-9}}$ daría un warning de NumPy y arruinaría el ajuste.

Físicamente, la ley cuadrática predice la **magnitud** de la corriente (el
flujo de huecos), no su signo. El signo depende de la convención de cómo se
conectan source y drain en el Keithley.

### Una advertencia honesta

La ley cuadrática es una aproximación. A $V_{GS}$ muy altos la movilidad
suele degradarse, y a $V_{GS}$ cerca de $V_{th}$ la aproximación deja de
valer. Por eso el $\sqrt{I_{DS}}$ vs $V_{GS}$ no es perfectamente recto en
todo el rango: tiene una zona lineal en el medio. Por eso la notebook tiene
un parámetro `vgs_range` para elegir **dónde** la recta ajusta bien.

---

## Resumen de las decisiones

| Decisión | Elegido | Por qué |
|---|---|---|
| Curva a usar | $V_{DS}$ más alta | Máxima probabilidad de estar en saturación |
| Tipo de dispositivo | p | $I_{DS}$ negativo, $V_{th} < 0$, se usa $\sqrt{|I_{DS}|}$ |
| Forward o reverse | Solo forward | Evita mezclar estados de histéresis |
| Orden de trabajo | Explorar → extraer | Verificar que el modelo aplica antes de fiarse del número |

---

## Glosario rápido

- **$V_{GS}$**: voltaje gate-source (lo que barres en una transfer).
- **$V_{DS}$**: voltaje drain-source (fijo durante una transfer).
- **$I_{DS}$**: corriente drain-source (lo que mides).
- **$V_{th}$**: threshold voltage. Voltaje de gate a partir del cual el
  canal se "abre" y empieza a conducir.
- **Pinchoff (pinch-off)**: punto donde el canal se estrangula cerca del
  drenador, marcando el inicio de la saturación.
- **Histeresis**: diferencia entre las curvas de subida y bajada de $V_{GS}$.
  En EGOFETs viene de la respuesta lenta de los ones del electrolito.
- **Ley cuadrática**: $I_{DS} \propto (V_{GS} - V_{th})^2$. Solo válida en
  saturación y asumiendo movilidad constante.
- **Linealización**: transformar una relación no-lineal (parábola) en una
  lineal (recta) para poder hacer regresión y extraer parámetros
  fácilmente. El método $\sqrt{I_{DS}}$ es exactamente eso.
