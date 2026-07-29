"""Functions to plot EGOFET measurements."""

import matplotlib.pyplot as plt
import numpy as np

from .readers.keithley_dean import list_measurements, read_all_curves, _has_hysteresis


def plot_transfer(hdf5_path, measurement_name, loop: bool=True, ax=None):
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
    loop : bool, opcional
        Si es True, grafica ambas curvas (forward y reverse).
        Si es False, grafica solo la curva forward.
        Default es True.
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
        
        if loop:
            if split is None:
                ax.plot(v_gs, i_ds, 'o-', ms=3, color=color,
                        label=f'{float(v_ds):.2f} V (#{curve_idx})')
            else:
                ax.plot(v_gs[:split+1], i_ds[:split+1], 'o-', ms=3,
                        color=color, label=f'{float(v_ds):.2f} V (#{curve_idx})')
                ax.plot(v_gs[split+1:], i_ds[split+1:], 'o--', ms=3,
                        color=color, label='_nolegend_')
        else:
            # Solo graficamos el forward
            ax.plot(v_gs[:split+1], i_ds[:split+1], 'o-', ms=3, color=color,
                    label=f'{float(v_ds):.2f} V (#{curve_idx})')

    ax.set_xlabel(r"$V_{GS}$ (V)")
    ax.set_ylabel(r"$I_{DS}$ (A)")
    ax.set_title(f"Transfer — {measurement_name}")
    ax.legend(fontsize=8, title=r'$V_{DS}$')
    ax.grid(True, alpha=0.3)

    return fig, ax

def plot_output(hdf5_path, measurement_name, ax=None):
    """Grafica todas las curvas de una medicion output desde un HDF5.

    Cada V_DS se dibuja con un color distinto.

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
        
        ax.plot(v_ds, i_ds, 'o-', ms=3, color=color,
                label=f'{float(v_gs[0]):.2f} V (#{curve_idx})')

    ax.set_xlabel(r"$V_{DS}$ (V)")
    ax.set_ylabel(r"$I_{DS}$ (A)")
    ax.set_title(f"Output — {measurement_name}")
    ax.legend(fontsize=8, title=r'$V_{GS}$')
    ax.grid(True, alpha=0.3)

    return fig, ax

def plot_i_vs_time(hdf5_path, measurement_name, array_time: np.ndarray, ax=None):
    """Grafica Ids vs time para una medicion i-vs-t desde un HDF5."""