"""Base functions for reading and inspecting HDF5 files."""

import h5py


def print_structure(hdf5_path, max_depth=3):
    """Print the group/dataset tree of an HDF5 file.

    Parameters
    ----------
    hdf5_path : str
        Path to the HDF5 file.
    max_depth : int
        Maximum depth to descend into groups (default 3).
    """
    def _walk(grp, prefix, depth):
        if depth > max_depth:
            return
        for key in sorted(grp.keys()):
            item = grp[key]
            if isinstance(item, h5py.Group):
                n_children = len(item.keys())
                attrs = dict(item.attrs)
                attr_str = ""
                if attrs:
                    attr_str = "  " + ", ".join(
                        f"{k}={v}" for k, v in attrs.items()
                    )
                print(f"{prefix}{key}/ [{n_children} children]{attr_str}")
                _walk(item, prefix + "  ", depth + 1)
            else:
                print(f"{prefix}{key}  shape={item.shape}  dtype={item.dtype}")

    with h5py.File(hdf5_path, 'r') as f:
        print(f"HDF5: {hdf5_path}")
        print(f"/ [{len(f.keys())} groups]")
        _walk(f, "  ", depth=1)

def view_tree_content(hdf5_path, attribute_name: str=None):
    """Imprime la estructura del HDF5 de forma visual y legible.
    
    Parameters
    ----------
    hdf5_path : str
        Path to the HDF5 file.
    attribute_name : str, optional
        Name of the attribute to print (default None).
    """
    with h5py.File(hdf5_path, 'r') as f:

        print(f"📁 / (Raíz del árbol)")
        
        # 1. Definimos la función interna que procesará cada curva/dataset
        def mostrar_elemento(name, obj):
            level = name.count('/')
            sangria = '  ' * (level + 1) # +1 para dar espacio respecto a la raíz
            short_name = name.split('/')[-1]
                
            if isinstance(obj, h5py.Group):
                if attribute_name:
                    print(f"{sangria}📁 {short_name}/  Atributo: {obj.attrs.get(attribute_name, 'Unknown')}")
                else:
                    print(f"{sangria}📁 {short_name}/")
            else:
                if attribute_name:
                    print(f"{sangria}⚡ {short_name} (Shape: {obj.shape}, Tipo: {obj.dtype}), Atributo: {obj.attrs.get(attribute_name, 'Unknown')}")
                else:
                    print(f"{sangria}⚡ {short_name} (Shape: {obj.shape}, Tipo: {obj.dtype})")
        
        # 2. Le pasamos esta función a visititems para que recorra el subgrupo
        f.visititems(mostrar_elemento)
