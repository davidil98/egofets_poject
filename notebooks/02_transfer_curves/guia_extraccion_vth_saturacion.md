# Guía de aprendizaje: Extracción de $V_{th}$ en saturación

Esta guía es el puente entre entender **qué es la saturación** (documento
anterior) y **sacar el número** del threshold voltage. Antes de pasar al
régimen lineal conviene tener este número bien anclado porque:

1. Es el dato que más se reporta en la literatura de OFETs/EGOFETs.
2. Define la frontera entre "canal apagado" y "canal encendido", así que
   todas las movilidades (lineal y saturación) se calculan respecto a él.
3. La pendiente del ajuste lineal de $\sqrt{|I_{DS}|}$ vs $V_{GS}$ te da
   gratis la movilidad en saturación, $\mu_{sat}$.

---

## 1. Recordatorio rápido: la fórmula que vamos a usar

En saturación, y suponiendo movilidad constante (suposición que después
verificaremos con los datos), la corriente drenaje-fuente en magnitud es:

$$
|I_{DS}^{sat}| \;=\; \frac{1}{2}\,\mu_{sat}\,C\,\frac{W}{L}\,\left(V_{GS} - V_{th}\right)^{2}
$$

Donde:

- $\mu_{sat}$: movilidad de los portadores en saturación (cm²/V·s).
- $C$: capacitancia por unidad de área de la doble capa eléctrica (F/cm²).
  En un EGOFET esta es mucho mayor que en un MOSFET porque la EDL es del
  orden de los nanómetros en vez de micrómetros.
- $W$, $L$: ancho y largo del canal (cm).
- $V_{th}$: threshold voltage (V). En tu dispositivo tipo p es **negativo**.

**Truco de linealización** (ya explicado en detalle en
`teoria_saturacion_y_vth.md`): tomando raíz cuadrada,

$$
\sqrt{|I_{DS}^{sat}|} \;=\; \underbrace{\sqrt{\tfrac{1}{2}\mu_{sat} C\,\tfrac{W}{L}}}_{\text{pendiente } m} \cdot \;\underbrace{\left(V_{GS} - V_{th}\right)}_{\text{forma } (x - b)}
$$

En la región de encendido ($V_{GS} > V_{th}$ para tipo p, donde $V_{th}<0$,
esto es siempre cierto para $V_{GS}$ del lado positivo), es una **recta**
con:

- **pendiente** $m = \sqrt{\tfrac{1}{2}\mu_{sat}\,C\,W/L}$
- **intercepto en el eje $V_{GS}$** en $V_{GS} = V_{th}$ (donde
  $\sqrt{|I_{DS}|} = 0$).

El método consiste en ajustar esa recta y leer el intercepto. Pero antes de
hacerlo "a ciegas", vamos a ver **cómo se hace bien**.

---

## 2. Procedimiento paso a paso

### Paso 2.1 — Elegir la curva correcta

**Estrategia: usar la transfer con $|V_{DS}|$ más alto disponible.**

Razón: la condición de saturación es $|V_{DS}| \geq |V_{GS} - V_{th}|$. Si
$V_{DS}$ es más grande, esa condición se cumple en un rango más amplio de
$V_{GS}$, y por tanto la ley cuadrática es válida en casi toda la curva.

En tu caso ya lo haces en la celda previa:

```python
i_max = max(range(len(curves)), key=lambda i: abs(curves[i]['v_ds']))
curve = curves[i_max]
```

Esto selecciona la curva con el $|V_{DS}|$ máximo. Buena estrategia como
primera apuesta, aunque la **prueba definitiva** es mirar la output curve
(en la notebook 03). Si en algún $V_{GS}$ ves la zona plana característica,
sabes que el dispositivo está saturando ahí.

### Paso 2.2 — Quedarse solo con el forward sweep

Los iones del electrolito responden lento a los cambios de $V_{GS}$. Cuando
barres $V_{GS}$ hacia un extremo y vuelves, los iones no se han terminado
de redistribuir: la curva de ida y la de vuelta no coinciden. Esto es la
**histéresis**.

La ley cuadrática asume un dispositivo en estado cuasi-estático. Si mezclas
forward y reverse, promedias dos estados físicos distintos y la parábola
deja de ajustar limpio.

**Por eso se hace:** `fwd_only=True` en `read_curve`, que ya tienes.

**Reporte:** luego se extrae también $V_{th}^{rev}$ por separado, y la
**diferencia** $\Delta V_{th} = V_{th}^{rev} - V_{th}^{fwd}$ es un
parámetro físico del dispositivo (qué tan "limpio" es el apilado
electrolito/semiconductor).

### Paso 2.3 — Calcular $\sqrt{|I_{DS}|}$

```python
sqrt_i = np.sqrt(np.abs(i_ds_fwd))
```

Por qué `abs`: en un EGOFET tipo p, $I_{DS}$ es negativo, del orden de
$10^{-9}$ a $10^{-6}$ A. Raíz de un número negativo es imaginaria; NumPy
te tira warning y arruina el ajuste. Físicamente, la ley cuadrática
predice la **magnitud** del flujo de huecos, no su signo.

### Paso 2.4 — Elegir la ventana de ajuste

Este es el paso más delicado. El $\sqrt{|I_{DS}|}$ vs $V_{GS}$ no es
perfectamente recto en todo el rango. Tiene:

- **Cerca del threshold** ($V_{GS} \approx V_{th}$): la aproximación de
  mobility constante falla porque la carga en el canal es pequeña y los
  efectos de atrapamiento (traps) dominan.
- **Lejos del threshold** ($V_{GS}$ muy positivo): la movilidad suele
  degradarse por scattering y otros efectos.

Por eso la curva es recta **solo en una zona del medio**, y hay que elegir
bien dónde ajustar. La idea estándar es probar con un par de ventanas y
ver cómo se mueve el $V_{th}$.

**Cómo se elige en la práctica:**

- **Opción A (automática):** ajustar en el rango donde la derivada
  segunda de $\sqrt{|I_{DS}|}$ es mínima (zona de menor curvatura).
- **Opción B (manual):** probar 2 o 3 ventanas y comparar resultados.
- **Opción C (visual):** graficar, mirar dónde la curva es recta, y usar
  esa ventana. Pedagógicamente la mejor, pero es la que más depende del ojo.

**Recomendación para empezar:** haz la **C** y luego la **B** para tener
confianza en el número. Más adelante, si quieres, automatizas con la A.

### Paso 2.5 — Ajuste lineal

```python
# m: pendiente, b: intercepto en V_GS
m, b = np.polyfit(v_gs_sel, sqrt_i_sel, 1)
V_th = b   # en saturación
```

Aquí `polyfit` de NumPy hace mínimos cuadrados ordinarios (no ponderados).
Para un primer análisis está bien; más adelante puedes ponderar por
$1/\sqrt{|I_{DS}|}$ si ves que los puntos de alta corriente dominan
demasiado el ajuste (suelen tener más peso porque su varianza absoluta es
mayor).

### Paso 2.6 — Reportar

- `V_th` con 3 decimales en volts.
- `m` con unidades consistentes (si $\sqrt{|I_{DS}|}$ está en $\sqrt{A}$ y
  $V_{GS}$ en V, entonces $m$ queda en $\sqrt{A}/V$).
- Idealmente, los **errores** de ambos (`np.polyfit` no los da
  directamente; para eso se usa `scipy.stats.linregress` o se calcula la
  covarianza de la matriz de diseño).

---

## 3. De la pendiente a la movilidad (bonus gratis)

Una vez que tienes $m$, la movilidad sale así:

$$
\mu_{sat} \;=\; \frac{2\,L}{W\,C}\cdot m^{2}
$$

**¡Ojo con las unidades!** Si usas SI todo ($W$, $L$ en m; $C$ en
F/m²; $I_{DS}$ en A), $\mu_{sat}$ sale en m²/V·s. Hay que convertir a
cm²/V·s multiplicando por $10^{4}$.

**Ejemplo numérico de control** (no es de tu dispositivo, es para chequear
órdenes de magnitud): en un EGOFET típico con $C \sim 10^{-6}$ F/cm²,
$W/L \sim 10$, si la pendiente del $\sqrt{|I_{DS}|}$ vs $V_{GS}$ es del
orden de $10^{-4}\,\sqrt{\text{A}}/\text{V}$, entonces:

$$
\mu_{sat} \;\sim\; \frac{2}{10 \cdot 10^{-6}}\cdot (10^{-4})^{2}
\;\sim\; 2 \times 10^{-3}\;\text{cm}^2/\text{V·s}
$$

Que está en el rango típico de semiconductores orgánicos (0.1 a 10
cm²/V·s, según material y procesamiento). Si te sale un número muy
distinto, hay algo mal en las unidades o en la elección de curva.

---

## 4. Cómo saber si el ajuste es bueno (diagnósticos)

Cuatro chequeos que vale la pena hacer **antes de fiarte** del número:

### 4.1 Coeficiente de determinación $R^2$

$$
R^{2} \;=\; 1 - \frac{\sum_{i}(y_i - \hat{y}_i)^{2}}{\sum_{i}(y_i - \bar{y})^{2}}
$$

Donde $y_i = \sqrt{|I_{DS}|}$ son los datos, $\hat{y}_i$ son los del
ajuste, y $\bar{y}$ la media. Si $R^2 < 0.95$ (o así), desconfía. En
EGOFETs a veces $R^2$ no llega a 0.99 como en un MOSFET de silicio, pero
debería estar cerca de 1.

### 4.2 Residuos

Graficar $r_i = y_i - \hat{y}_i$ vs $V_{GS}$. Si el ajuste es bueno, los
residuos deberían verse **aleatorios** alrededor de cero, sin patrón.
Si ves una forma de "U" o de "U invertida", el rango elegido no es el
adecuado (la parábola se está curvando dentro de la ventana).

### 4.3 Pendiente vs offset

Otro test: si duplicas el rango de $V_{GS}$ y el $V_{th}$ cambia más de,
digamos, 50 mV, probablemente la ventana de ajuste no es estable y el
número no es robusto. Reporta siempre con qué ventana se extrajo.

### 4.4 Coherencia física

- $V_{th}$ debe estar **a la izquierda** del primer $V_{GS}$ donde
  $I_{DS}$ empieza a crecer rápido (en tipo p, más negativo).
- La pendiente $m$ debe ser **positiva** (porque $\sqrt{|I_{DS}|}$ sube
  con $V_{GS}$ en tipo p).
- Si $|V_{th}| > |V_{GS}^{min}|$ (el $V_{GS}$ más bajo de tu barrido),
  estás fuera de la zona de encendido y el método no aplica.

---

## 5. Resumen de decisiones para tu dispositivo

| Decisión | Qué hacer | Por qué |
|---|---|---|
| Curva | $\|V_{DS}\|$ máximo | Máxima probabilidad de estar en saturación |
| Sweep | Solo forward | Evita mezclar estados de histéresis |
| Variable | $\sqrt{\|I_{DS}\|}$ vs $V_{GS}$ | Linealiza la parábola |
| Ajuste | `np.polyfit(..., 1)` en ventana elegida | Mínimos cuadrados, lectura directa del intercepto |
| Resultado | $V_{th} = b$, con $R^2$ como diagnóstico | Reportable y verificable |
| Bonus | $\mu_{sat} = (2L/WC) \cdot m^2$ | Sale gratis de la misma pendiente |

---

## 6. Pequeñas trampas numéricas a evitar

1. **No tomar $\sqrt{|I_{DS}|}$ donde $I_{DS} \approx 0$** (cerca del
   threshold o en la zona off). El ruido domina y arruina el ajuste. Por
   eso se restringe a la región on.
2. **Cuidado con la convención de signo.** En tu dispositivo $I_{DS} < 0$
   y $V_{th} < 0$. Si la recta ajustada da $b > 0$, probablemente estás
   usando $I_{DS}$ con signo en vez de $|I_{DS}|$, o confundiendo el
   sentido del barrido.
3. **No extrapolar.** Lee el $V_{th}$ solo donde hay datos. Si el
   intercepto cae fuera del rango barrido, reporta con cuidado (puede
   estar bien o puede ser artefacto del ajuste).
4. **Revisa las unidades de $C$.** La doble capa eléctrica en EGOFETs se
   suele reportar en $\mu$F/cm², no en F/cm². Un factor de $10^{6}$ se
   arrastra muy fácil.

---

## 7. Después de $V_{th}$ en saturación, ¿qué sigue?

Una vez que tengas $V_{th}^{fwd}$ sólido:

1. **Comparar con la output curve** (notebook 03): verifica que en la
   zona donde ajustaste, el dispositivo realmente está saturando (es
   decir, $I_{DS}$ no depende de $V_{DS}$ para $V_{GS}$ fijo).
2. **Extraer $\mu_{sat}$** con la fórmula de la sección 3.
3. **Histeresis:** extraer $V_{th}^{rev}$ con el mismo método y reportar
   $\Delta V_{th} = V_{th}^{rev} - V_{th}^{fwd}$.
4. **Recién después pasar al régimen lineal**, donde la fórmula es
   distinta y la movilidad que sale ($\mu_{lin}$) se puede comparar con
   $\mu_{sat}$. La relación $\mu_{sat}/\mu_{lin}$ te dice cuánto afecta
   el campo vertical al transporte (un número físico importante).
5. **Subthreshold swing** ($SS$): una vez que tienes $V_{th}$ bien
   definido, ajustas la zona subumbral (entre off y on) y extraes $SS$.

---

## Glosario rápido (añadido al del documento anterior)

- **Forward sweep**: la curva medida mientras $V_{GS}$ se barre de un
  extremo al otro (típicamente de positivo a negativo en tipo p).
- **Reverse sweep**: la curva de vuelta, de negativo a positivo.
- **Ajuste lineal (linear fit)**: encontrar la recta que mejor pasa por
  los datos en el sentido de mínimos cuadrados.
- **Residuos**: diferencia entre los datos y el ajuste. Si el modelo es
  correcto, deberían verse aleatorios.
- **$R^2$**: coeficiente de determinación. Mide qué tanto de la
  varianza de los datos explica el modelo. 1 = perfecto, 0 = nada.
- **$\Delta V_{th}$**: diferencia entre $V_{th}$ del reverse y forward.
  Parámetro de histéresis. En EGOFETs bien fabricados, del orden de
  décenas de mV; valores grandes (cientos de mV) indican respuesta iónica
  lenta.
