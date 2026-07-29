"""Modulo para extraer parametros de mediciones EGOFET."""

import numpy as np
import pandas as pd
from scipy.stats import linregress

from .readers.keithley_dean import read_all_curves, read_curve


def extract_vth_for_transfers(
    hdf5_path, measurements,
    v_min_range=(-0.40, -0.20),
    v_max_range=(-0.15, -0.05),
    step=0.01,
    min_points=5,
):
    """Extrae V_th de multiples mediciones transfer con busqueda 2D de ventana.

    Para cada medicion:
      - Toma la curva con |V_DS| maximo (saturacion).
      - Calcula sqrt(|I_DS|) en el forward sweep.
      - Busca la mejor combinacion (v_min, v_max) dentro del rectangulo
        definido que maximice R^2.
      - Calcula V_th = -intercept/slope de la regresion lineal en esa ventana.

    Parameters
    ----------
    hdf5_path : str o Path
    measurements : list[str]
        Nombres de mediciones de tipo transfer.
    v_min_range, v_max_range : tuple
        (min, max) del extremo izquierdo/derecho de la ventana, en V.
    step : float
        Resolucion de la busqueda en V.
    min_points : int
        Minimo de puntos para aceptar un fit.

    Returns
    -------
    pd.DataFrame
        Columnas: measurement, V_DS (V), V_th (V), v_min (V), v_max (V),
        R^2, n_points.
    """
    results = []
    for m_name in measurements:
        try:
            curves = read_all_curves(hdf5_path, m_name)
            i_max = max(range(len(curves)), key=lambda i: abs(curves[i]['v_ds'][0]))
            curve = curves[i_max]

            v_gs_fwd, i_ds_fwd = read_curve(
                hdf5_path, m_name, curve['curve_name'], fwd_only=True
            )
            sqrt_ids = np.sqrt(np.abs(i_ds_fwd))

            best_r2 = -np.inf
            best_params = None
            for v_min in np.arange(v_min_range[0], v_min_range[1], step):
                for v_max in np.arange(v_max_range[0], v_max_range[1], step):
                    if v_max <= v_min:
                        continue
                    mask = (v_gs_fwd >= v_min) & (v_gs_fwd <= v_max)
                    if mask.sum() < min_points:
                        continue
                    slope, intercept, r_value, _, _ = linregress(
                        v_gs_fwd[mask], sqrt_ids[mask]
                    )
                    r2 = r_value**2
                    if r2 > best_r2:
                        best_r2 = r2
                        best_params = (v_min, v_max, slope, intercept, mask.sum())

            if best_params is None:
                print(f"{m_name}: ninguna ventana valida en el rectangulo")
                continue

            v_min, v_max, slope, intercept, n_pts = best_params
            v_th = -intercept / slope

            results.append({
                'measurement': m_name,
                'V_DS (V)': curve['v_ds'][0],
                'V_th (V)': v_th,
                'v_min (V)': v_min,
                'v_max (V)': v_max,
                'R^2': best_r2,
                'n_points': n_pts,
            })
        except Exception as e:
            print(f"{m_name}: {e}")
            continue

    return pd.DataFrame(results)
