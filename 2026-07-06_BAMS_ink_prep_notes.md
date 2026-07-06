# Notas de Preparación de Tinta — BAMS 2026-07-07

**Fecha de preparación:** 2026-07-06
**Fecha de uso (BAMS):** 2026-07-07
**Protocolo de referencia:** `egofets-project/docs/OSC Ink Fabrication Protocol.docx`

## 1. Objetivo

Preparar tinta semiconductora 2% diFT:PS en proporción 4:1 (OSC:PS) en clorobenceno (CB) para depositar por BAMS mañana sobre **4 dispositivos** (1 wafer, 1 pieza).

## 2. Cantidades a pesar (corregidas)

| Reactivo                  | Masa   | CB         | Concentración | Notas                       |
|---------------------------|--------|------------|---------------|-----------------------------|
| diFT-TES-ADT (SC)         | 4 mg   | 200 µL     | 20 mg/mL (2%) | Vial ámbar, fotosensible    |
| Poliestireno (PS, 10 kDa) | 4 mg   | 200 µL     | 20 mg/mL (2%) | Vial incoloro               |

> **Verificación**: 4 mg / 200 µL = 20 mg/mL ≈ 2% p/v ✓ (objetivo: 22.6 mg/mL, está dentro del margen del 12% — aceptable para la práctica).

## 3. Procedimiento (resumen del protocolo)

### 3.1 Extracción de CB
1. Hinchar globo con Ar usando aguja pequeña (sirve como septum).
2. Con jeringa + aguja grande, extraer CB del frasco (sin tumbarlo).
3. Transferir 2 mL a un vial ámbar limpio.

### 3.2 Disolución (viales separados)
1. Pesar **4 mg de diFT** en vial ámbar, añadir 200 µL de CB.
2. Pesar **4 mg de PS** en vial incoloro, añadir 200 µL de CB.
3. Tapar con Al foil. Llevar al BAMS a **105 °C durante ≥ 60 min**.

### 3.3 Mezcla 4:1 (mañana, antes de BAMS)

> ⚠️ **Importante**: la mezcla 4:1 NO es 4:1 en masa sino en volumen de cada disolución. La cantidad final se ajusta mañana según cuántos dispositivos vayas a procesar.

Regla:
- Por cada **4 partes** de solución de diFT, añadir **1 parte** de solución de PS.

Ejemplo para 4 dispositivos (≈ 140 µL de tinta final):
- Solución de diFT necesaria: 4/5 × 140 = **112 µL**
- Solución de PS necesaria:   1/5 × 140 = **28 µL**
- Mezclar en el vial de diFT, NO en el de PS (es fotosensible).

Pasos:
1. Calcular el volumen total necesario (4 disp × 35 µL = 140 µL mínimo, +20% por pérdidas).
2. Extraer con micropipeta el volumen de solución de PS calculado.
3. Inyectar en el vial de diFT, despacio y por las paredes.
4. Bajar temperatura del hot plate a **60 °C**.
5. Mantener 15-30 min en el hotplate para homogeneizar antes del BAMS.

## 4. Checklist pre-BAMS (mañana 2026-07-07)

- [ ] Vial con tinta 4:1 a 60 °C, homogenizada 15-30 min
- [ ] Bar #3 limpio (acetona + IPA + N2)
- [ ] Hotplate del BAMS a 105 °C, bar precalentado 30-60 min
- [ ] Vial de tinta sobre el hotplate mientras se procesan los 4 dispositivos
- [ ] CB entre el hotplate y la muestra para fijación
- [ ] 30-40 µL de tinta por dispositivo
- [ ] Pipeta de vidrio para colocar la tinta en la parte superior/central del bar
- [ ] Guía de canales: 10 mm/s, 2778 motor steps/s

## 5. Después del BAMS

- [ ] Guardar dispositivos en vacío/glovebox (EGOFETs son sensibles a humedad)
- [ ] Anotar pesos reales en la BD con el notebook `template_ink_prep.ipynb`
- [ ] Si sobra tinta del vial, etiquetar con fecha y proporción — dura unos días en glovebox
