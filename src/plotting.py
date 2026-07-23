"""Functions to plot EGOFET measurements."""

import matplotlib.pyplot as plt
import numpy as np

from .readers.keithley_dean import list_measurements, read_all_curves


def _has_hysteresis(v_gs):
    """Devuelve el indice de quiebre si la curva tiene forward+reverse, o None."""
    signs = np.sign(np.diff(v_gs))
    signs = signs[signs != 0]
    changes = np.where(np.diff(signs) != 0)[0]
    if len(changes) == 0:
        return None
    return changes[0] + 1


def plot_transfer(hdf5_path, measurement_name, ax=None):
    """Grafica todas las curvas de una medicion transfer desde un HDF5.

    Cada V_DS se dibuja con un color distinto. Si la curva tiene ida y vuelta
    (histeresis), el forward se dibuja con linea solida y el reverse con
    linea discontinua del mismo color.

    Parameters
    ----------
    hdf5_path : str o Path
        Ruta al archivo HDF5.
    measurement_name : str
        Nombre del grupo top-level dentro del HDF5.
    ax : matplotlib.axes.Axes, opcional
        Ejes donde graficar. Si es None, se crea una figura nueva.

    Returns
    -------
    fig, ax
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 5))
    else:
        fig = ax.figure

    colors = plt.cm.tab10.colors
    curves = read_all_curves(hdf5_path, measurement_name)

    for i, c in enumerate(curves):
        v_gs = c['v_gs']
        i_ds = c['i_ds']
        v_ds = c['v_ds']
        curve_name = c['curve_name']
        curve_idx = curve_name.split('_')[-1]
        color = colors[i % len(colors)]

        split = _has_hysteresis(v_gs)
        if split is None:
            ax.plot(v_gs, i_ds, 'o-', ms=3, color=color,
                    label=f'{float(v_ds):.2f} V (#{curve_idx})')
        else:
            ax.plot(v_gs[:split+1], i_ds[:split+1], 'o-', ms=3,
                    color=color, label=f'{float(v_ds):.2f} V (#{curve_idx})')
            ax.plot(v_gs[split+1:], i_ds[split+1:], 'o--', ms=3,
                    color=color, label='_nolegend_')

    ax.set_xlabel(r"$V_{GS}$ (V)")
    ax.set_ylabel(r"$I_{DS}$ (A)")
    ax.set_title(f"Transfer — {measurement_name}")
    ax.legend(fontsize=8, title=r'$V_{DS}$')
    ax.grid(True, alpha=0.3)

    return fig, ax

def plot_i_vs_time(hdf5_path, measurement_name, array_time: np.ndarray, ax=None):
    """Grafica Ids vs time para una medicion i-vs-t desde un HDF5."""
    
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 5))
    else:
        fig = ax.figure
    
    colors = plt.cm.tab10.colors
    curves = read_all_curves(hdf5_path, measurement_name)

    for i, c in enumerate(curves):
        i_ds = c['i_ds']
        time = array_time
        curve_name = c['curve_name']
        curve_idx = curve_name.split('_')[-1]
        color = colors[i % len(colors)]

        ax.plot(time, i_ds, 'o-', ms=3, color=color,
                    label=f'Curve #{curve_idx}')

    ax.set_xlabel(r"$t$ (s)")
    ax.set_ylabel(r"$I_{DS}$ (A)")
    ax.set_title(f"I-vs-t — {measurement_name}")
    ax.legend(fontsize=8, title=r'Curve')
    ax.grid(True, alpha=0.3)

    return fig, ax