"""Module for reading Keithley 2450 HDF5 files configured by Dean.

Each top-level group is a measurement. Its structure:
    measurement/
        attrs: measurement_mode ("transfer", "output", ...)
        curve_000/
            measured_V_GS    dataset  (transfer) o measured_V_DS (output)
            measured_I_DS    dataset
            attrs: V_DS (transfer) o V_GS (output)
        curve_001/
            ...
"""

import h5py
import os
import numpy as np


def list_measurements(hdf5_path):
    """List all measurements in a Keithley HDF5 file.

    Returns a list of dicts with keys: name, mode, n_curves.
    """
    measurements = []
    with h5py.File(hdf5_path, 'r') as f:
        for name in sorted(f.keys()):
            group = f[name]
            mode = group.attrs.get('measurement_mode', 'desconocido')
            n_curves = len([k for k in group.keys() if k.startswith('curve_')])
            measurements.append({
                'name': name,
                'mode': mode,
                'n_curves': n_curves,
            })
    return measurements

def view_measurements(hdf5_path):
    """Read the measurement names and print them in a format like table.
    
    Returns a str."""

    with h5py.File(hdf5_path, 'r') as f:
        print(f"Archivo: {os.path.basename(hdf5_path)}")
        print(f"Mediciones encontradas ({len(f.keys())}):\n")

        lines = []
        for name in sorted(f.keys()):
            group = f[name]
            mode = group.attrs.get('measurement_mode', 'desconocido')
            n_curves = len([k for k in group.keys() if k.startswith('curve_')])
            lines.append(f"  {name:50s}  mode={mode:10s}  curves={n_curves}")

        str_data = '\n'.join(lines)
        print(str_data)
        return str_data

def get_dset_names(hdf5_path, measurement_name):
    """Get the dataset names from a measurement.
    
    Returns a list of dicts with keys: name, shape, dtype, attrs.
    """
    datasets = []
    with h5py.File(hdf5_path, 'r') as f:
        group = f[measurement_name]
        for name in sorted(group.keys()):
            dataset = group[name]
            datasets.append({
                'name': name,
                'shape': dataset.shape,
                'dtype': dataset.dtype,
                'attrs': dict(dataset.attrs),
            })
    return datasets

def get_dset_array(hdf5_path, measurement_name, dsets: list = None) -> tuple:
    """Get the array from a dataset.
    
    Returns a numpy array for each dataset. If not specified, return all dsets.

    Parameters
    ----------
    hdf5_path : str
        Path to the HDF5 file.
    measurement_name : str
        Name of the measurement group.
    dsets : list, optional
        List of dataset names to read. If None, all datasets are read.

    Returns
    =======
    tuple
        Tuple of numpy arrays.
    
    Example:
    
    value1, value2, ... valueN = get_dset_array(hdf5_path, measurement_name, dsets=['measured_V_GS', 'measured_I_DS', ...])

    or

    dset1, dset2, *others = get_dset_array(hdf5_path, measurement_name)
    """

    dsets_list = []

    with h5py.File(hdf5_path, 'r') as f:
        group = f[measurement_name]
        if dsets is None:
            dsets = sorted(group.keys())
        
        for name in dsets:
            dataset = group[name]
            dsets_list.append(dataset[:])
    
    return tuple(dsets_list)

def _has_hysteresis(v_gs):
    """Devuelve el indice de quiebre si la curva tiene forward+reverse, o None."""
    signs = np.sign(np.diff(v_gs))
    signs = signs[signs != 0]
    changes = np.where(np.diff(signs) != 0)[0]
    if len(changes) == 0:
        return None
    return changes[0] + 1

def read_curve(hdf5_path, measurement_name, curve_name='curve_000', fwd_only: bool = True):
    """Read V_GS and I_DS from a single transfer curve.

    Returns v_gs, i_ds as numpy arrays.
    
    Parameters
    ----------
    hdf5_path : str
        Path to the HDF5 file.
    measurement_name : str
        Name of the measurement group.
    curve_name : str, optional
        Name of the curve to read. Default is 'curve_000'.
    fwd_only : bool, optional
        If True, return the forward curve. If False, return the fwd + reverse curve.
    """
    with h5py.File(hdf5_path, 'r') as f:
        curve = f[measurement_name][curve_name]
        if fwd_only:
            split = _has_hysteresis(curve['measured_V_GS'][:])
            v_gs = curve['measured_V_GS'][:split+1]
            i_ds = curve['measured_I_DS'][:split+1]
        else:
            v_gs = curve['measured_V_GS'][:]
            i_ds = curve['measured_I_DS'][:]
    return v_gs, i_ds


def read_all_curves(hdf5_path, measurement_name):
    """Read all curves from a measurement.

    Returns a list of dicts with keys: v_gs, i_ds, v_ds, curve_name.
    """
    curves = []
    with h5py.File(hdf5_path, 'r') as f:
        group = f[measurement_name]
        for curve_name in sorted(group.keys()):
            curve = group[curve_name]
            v_gs = curve['measured_V_GS'][:]
            i_ds = curve['measured_I_DS'][:]
            v_ds = curve.attrs.get('V_DS', None)
            curves.append({
                'v_gs': v_gs,
                'i_ds': i_ds,
                'v_ds': v_ds,
                'curve_name': curve_name,
            })
    return curves
