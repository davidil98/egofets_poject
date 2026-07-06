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


def read_curve(hdf5_path, measurement_name, curve_name='curve_000'):
    """Read V_GS and I_DS from a single transfer curve.

    Returns v_gs, i_ds as numpy arrays.
    """
    with h5py.File(hdf5_path, 'r') as f:
        curve = f[measurement_name][curve_name]
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
