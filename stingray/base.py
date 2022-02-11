"""Base classes"""
from collections.abc import Iterable
from abc import ABCMeta
import pickle
import warnings

import numpy as np
from astropy.table import Table


class StingrayObject(metaclass=ABCMeta):
    """This base class defines some general-purpose utilities.

    The main purpose is to have a consistent mechanism for:

    + round-tripping to and from Astropy Tables and other dataframes

    + round-tripping to files in different formats

    The idea is that any object inheriting :class:`StingrayObject` should,
    just by defining an attribute called ``main_array_attr``, be able to perform
    the operations above, with no additional effort.

    ``main_array_attr`` is, e.g. ``time`` for :class:`EventList` and
    :class:`Lightcurve`, ``freq`` for :class:`Crossspectrum`, ``energy`` for
    :class:`VarEnergySpectrum`, and so on. It is the array with wich all other
    attributes are compared: if they are of the same shape, they get saved as
    columns of the table/dataframe, otherwise as metadata.
    """

    def __init__(self):
        if not hasattr(self, "main_array_attr"):
            raise RuntimeError(
                "A StingrayObject needs to have the main_array_attr attribute specified"
            )

    def array_attrs(self):
        """List the names of the array attributes of the Stingray Object.

        By array attributes, we mean the ones with the same size and shape as
        ``main_array_attr`` (e.g. ``time`` in ``EventList``)
        """

        main_attr = getattr(self, getattr(self, "main_array_attr"))
        if main_attr is None:
            return []

        return [
            attr
            for attr in dir(self)
            if (
                isinstance(getattr(self, attr), Iterable)
                and np.shape(getattr(self, attr)) == np.shape(main_attr)
            )
        ]

    def meta_attrs(self):
        """List the names of the meta attributes of the Stingray Object.

        By array attributes, we mean the ones with a different size and shape
        than ``main_array_attr`` (e.g. ``time`` in ``EventList``)
        """
        array_attrs = self.array_attrs()
        return [
            attr
            for attr in dir(self)
            if (
                attr not in array_attrs
                and not attr.startswith("_")
                # Use new assignment expression (PEP 572). I'm testing that
                # self.attribute is not callable, and assigning its value to
                # the variable attr_value for further checks
                and not callable(attr_value := getattr(self, attr))
                # a way to avoid EventLists, Lightcurves, etc.
                and not hasattr(attr_value, "meta_attrs")
            )
        ]

    def get_meta_dict(self):
        """Give a dictionary with all non-None meta attrs of the object."""
        meta_attrs = self.meta_attrs()
        meta_dict = {}
        for key in meta_attrs:
            val = getattr(self, key)
            if val is not None:
                meta_dict[key] = val
        return meta_dict

    def to_astropy_table(self):
        """Save the Stingray Object to an Astropy Table.

        Array attributes (e.g. ``time``, ``pi``, ``energy``, etc. for
        ``EventList``) are converted into columns, while meta attributes
        (``mjdref``, ``gti``, etc.) are saved into the ``meta`` dictionary.
        """
        data = {}
        array_attrs = self.array_attrs()

        for attr in array_attrs:
            data[attr] = np.asarray(getattr(self, attr))

        ts = Table(data)

        ts.meta.update(self.get_meta_dict())

        return ts

    @classmethod
    def from_astropy_table(cls, ts):
        """Create a Stingray Object object from data in an Astropy Table.

        The table MUST contain at least a column named like the
        ``main_array_attr``.
        The rest of columns will form the array attributes of the
        new object, while the attributes in ds.attrs will
        form the new meta attributes of the object.

        It is strongly advisable to define such attributes and columns
        using the standard attributes of the wanted StingrayObject (e.g.
        ``time``, ``pi``, etc. for ``EventList``)
        """

        if len(ts) == 0:
            # return an empty object
            return cls

        array_attrs = ts.colnames

        # Set the main attribute first
        mainarray = np.array(ts[cls.main_array_attr])
        setattr(cls, cls.main_array_attr, mainarray)

        for attr in array_attrs:
            if attr == cls.main_array_attr:
                continue
            setattr(cls, attr, np.array(ts[attr]))

        for key, val in ts.meta.items():
            setattr(cls, key, val)

        return cls

    def to_xarray(self):
        """Save the :class:`StingrayObject` to an xarray Dataset.

        Array attributes (e.g. ``time``, ``pi``, ``energy``, etc. for
        ``EventList``) are converted into columns, while meta attributes
        (``mjdref``, ``gti``, etc.) are saved into the ``ds.attrs`` dictionary.
        """
        from xarray import Dataset

        data = {}
        array_attrs = self.array_attrs()

        for attr in array_attrs:
            data[attr] = np.asarray(getattr(self, attr))

        ts = Dataset(data)

        ts.attrs.update(self.get_meta_dict())

        return ts

    @classmethod
    def from_xarray(cls, ts):
        """Create an `EventList` object from data in an xarray Dataset.

        The dataset MUST contain at least a column named like the
        ``main_array_attr``.
        The rest of columns will form the array attributes of the
        new object, while the attributes in ds.attrs will
        form the new meta attributes of the object.

        It is strongly advisable to define such attributes and columns
        using the standard attributes of the wanted StingrayObject (e.g.
        ``time``, ``pi``, etc. for ``EventList``)
        """
        if len(ts) == 0:
            # return an empty object
            return cls

        array_attrs = ts.coords

        # Set the main attribute first
        mainarray = np.array(ts[cls.main_array_attr])
        setattr(cls, cls.main_array_attr, mainarray)

        for attr in array_attrs:
            if attr == cls.main_array_attr:
                continue
            setattr(cls, attr, np.array(ts[attr]))

        for key, val in ts.attrs.items():
            if key not in array_attrs:
                setattr(cls, key, val)

        return cls

    def to_pandas(self):
        """Save the :class:`StingrayObject` to a pandas DataFrame.

        Array attributes (e.g. ``time``, ``pi``, ``energy``, etc. for
        ``EventList``) are converted into columns, while meta attributes
        (``mjdref``, ``gti``, etc.) are saved into the ``ds.attrs`` dictionary.
        """
        from pandas import DataFrame

        data = {}
        array_attrs = self.array_attrs()

        for attr in array_attrs:
            data[attr] = np.asarray(getattr(self, attr))

        ts = DataFrame(data)

        ts.attrs.update(self.get_meta_dict())

        return ts

    @classmethod
    def from_pandas(cls, ts):
        """Create an `StingrayObject` object from data in a pandas DataFrame.

        The dataframe MUST contain at least a column named like the
        ``main_array_attr``.
        The rest of columns will form the array attributes of the
        new object, while the attributes in ds.attrs will
        form the new meta attributes of the object.

        It is strongly advisable to define such attributes and columns
        using the standard attributes of the wanted StingrayObject (e.g.
        ``time``, ``pi``, etc. for ``EventList``)

        """
        if len(ts) == 0:
            # return an empty object
            return cls

        array_attrs = ts.columns

        # Set the main attribute first
        mainarray = np.array(ts[cls.main_array_attr])
        setattr(cls, cls.main_array_attr, mainarray)

        for attr in array_attrs:
            if attr == cls.main_array_attr:
                continue
            setattr(cls, attr, np.array(ts[attr]))

        for key, val in ts.attrs.items():
            if key not in array_attrs:
                setattr(cls, key, val)

        return cls

    @classmethod
    def read(cls, filename, fmt=None, format_=None):
        r"""Generic reader for :class`StingrayObject`

        Currently supported formats are

        * pickle (not recommended for long-term storage)
        * any other formats compatible with the writers in
          :class:`astropy.table.Table` (ascii.ecsv, hdf5, etc.)

        Files that need the :class:`astropy.table.Table` interface MUST contain
        at least a column named like the ``main_array_attr``.
        The default ascii format is enhanced CSV (ECSV). Data formats
        supporting the serialization of metadata (such as ECSV and HDF5) can
        contain all attributes such as ``mission``, ``gti``, etc with
        no significant loss of information. Other file formats might lose part
        of the metadata, so must be used with care.

        ..note::

            Complex values can be dealt with out-of-the-box in some formats
            like HDF5 or FITS, not in others (e.g. all ASCII formats).
            With these formats, and in any case when fmt is ``None``, complex
            values should be stored as two real columns ending with ".real" and
            ".imag".

        Parameters
        ----------
        filename: str
            Path and file name for the file to be read.

        fmt: str
            Available options are 'pickle', 'hea', and any `Table`-supported
            format such as 'hdf5', 'ascii.ecsv', etc.

        Returns
        -------
        obj: :class:`StingrayObject` object
            The object reconstructed from file
        """
        if fmt is None and format_ is not None:
            warnings.warn("The format_ keyword for read and write is deprecated. Use fmt instead", DeprecationWarning)
            fmt = format_

        if fmt is None:
            pass
        elif fmt.lower() == "pickle":
            with open(filename, "rb") as fobj:
                return pickle.load(fobj)
        elif fmt.lower() == "ascii":
            fmt = "ascii.ecsv"

        ts = Table.read(filename, format=fmt)

        # For specific formats, and in any case when the format is not
        # specified, make sure that complex values are treated correctly.
        if fmt is None or "ascii" in fmt:
            for col in ts.colnames:
                if not (
                    (is_real := col.endswith(".real"))
                    or (is_imag := col.endswith(".imag"))
                ):
                    continue

                new_value = ts[col]

                if is_imag:
                    new_value = new_value * 1j

                # Make sure it's complex, even if we find the real part first
                new_value = new_value + 0.0j

                col_strip = col.replace(".real", "").replace(".imag", "")

                if col_strip not in ts.colnames:
                    # If the column without ".real" or ".imag" doesn't exist,
                    # define it, and make sure it's complex-valued
                    ts[col_strip] = new_value
                else:
                    # If it does exist, sum the new value to it.
                    ts[col_strip] += new_value

                ts.remove_column(col)

        return cls.from_astropy_table(ts)

    def write(self, filename, fmt=None, format_=None):
        """Generic writer for :class`StingrayObject`

        Currently supported formats are

        * pickle (not recommended for long-term storage)
        * any other formats compatible with the writers in
          :class:`astropy.table.Table` (ascii.ecsv, hdf5, etc.)

        ..note::

            Complex values can be dealt with out-of-the-box in some formats
            like HDF5 or FITS, not in others (e.g. all ASCII formats).
            With these formats, and in any case when fmt is ``None``, complex
            values will be stored as two real columns ending with ".real" and
            ".imag".

        Parameters
        ----------
        filename: str
            Name and path of the file to save the object list to.

        fmt: str
            The file format to store the data in.
            Available options are ``pickle``, ``hdf5``, ``ascii``, ``fits``
        """
        if fmt is None and format_ is not None:
            warnings.warn("The format_ keyword for read and write is deprecated. Use fmt instead", DeprecationWarning)
            fmt = format_
        if fmt is None:
            pass
        elif fmt.lower() == "pickle":
            with open(filename, "wb") as fobj:
                pickle.dump(self, fobj)
            return
        elif fmt.lower() == "ascii":
            fmt = "ascii.ecsv"

        ts = self.to_astropy_table()
        if fmt is None or "ascii" in fmt:
            for col in ts.colnames:
                if np.iscomplex(ts[col][0]):
                    ts[f"{col}.real"] = ts[col].real
                    ts[f"{col}.imag"] = ts[col].imag
                    ts.remove_column(col)

        try:
            ts.write(filename, format=fmt, overwrite=True, serialize_meta=True)
        except TypeError:
            ts.write(filename, format=fmt, overwrite=True)
