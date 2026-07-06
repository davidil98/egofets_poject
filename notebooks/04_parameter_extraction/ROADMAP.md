# Roadmap — test_graphics.ipynb

Reconstrucción paso a paso del notebook y los módulos src/.

| # | Paso | Notebook | src/ afectado | Estado |
|---|---|---|---|---|
| 1 | Setup: imports, rutas, listar archivos | ✅ celda[0] | — | done |
| 2 | Abrir HDF5 y listar grupos top-level (mediciones) | ✅ celda[1] | — | done |
| 3 | Leer UNA sola curva (curve_000, datos I_DS vs V_GS) | ✅ celda[2] | — | done |
| 4 | Primer gráfico simple: I_DS vs V_GS con `'o-'` | ✅ celda[3] | — | done |
| 5 | Detectar forward/reverse (dirección del barrido en V_GS) | ✅ celda[4] | — | done |
| 6 | Graficar forward y reverse separados (histéresis visible) | ✅ celda[5] | — | done |
| 7 | Iterar múltiples curvas de una medición, colores por V_DS | ✅ celda[6] | — | done |
| 8 | Función reutilizable: `plot_transfer_curve(hdf5_path, measurement_name)` | ⬜ | `plotting.py` | pending |

---

## Convenciones

- **Cada paso** es una o más celdas nuevas en `test_graphics.ipynb`.
- **Los módulos `src/`** se reescriben simultáneamente, pero solo con lo que entendamos en ese paso.
- **No se usa código preexistente** que no hayamos reconstruido juntos.
- Marcamos ✅ cuando el paso está implementado y comprendido.
