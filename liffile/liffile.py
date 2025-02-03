# liffile.py

# Copyright (c) 2023-2025, Christoph Gohlke
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""Read Leica image files (LIF and LOF).

Liffile is a Python library to read image and metadata from Leica image file
formats: LIF (Leica Image File) and LOF (Leica Object File).

These files are written by LAS X software to store collections of images
and metadata from microscopy experiments.

:Author: `Christoph Gohlke <https://www.cgohlke.com>`_
:License: BSD 3-Clause
:Version: 2025.2.2
:DOI: `10.5281/zenodo.14740657 <https://doi.org/10.5281/zenodo.14740657>`_

Quickstart
----------

Install the liffile package and all dependencies from the
`Python Package Index <https://pypi.org/project/liffile/>`_::

    python -m pip install -U liffile[all]

See `Examples`_ for using the programming interface.

Source code and support are available on
`GitHub <https://github.com/cgohlke/liffile>`_.

Requirements
------------

This revision was tested with the following requirements and dependencies
(other versions may work):

- `CPython <https://www.python.org>`_ 3.10.11, 3.11.9, 3.12.8, 3.13.1 64-bit
- `NumPy <https://pypi.org/project/numpy>`_ 2.2.2
- `Xarray <https://pypi.org/project/xarray>`_ 2025.1.2 (recommended)
- `Matplotlib <https://pypi.org/project/matplotlib/>`_ 3.10.0 (optional)
- `Tifffile <https://pypi.org/project/tifffile/>`_ 2025.1.10 (optional)

Revisions
---------

2025.2.2

- Add LifFlimImage class.
- Derive LifImage and LifFlimImage from LifImageABC.
- Rename LifImage.guid property to uuid (breaking).
- Add LifFile.uuid property.

2025.1.31

- Support LOF files.
- Make LifFile.xml_header a function (breaking).

2025.1.30

- Remove LifFile.flim_rawdata (breaking).
- Add index, guid, and xml_element_smd properties to LifImage.

2025.1.26

- Fix image coordinate values.
- Prompt for file name if main is called without arguments.

2025.1.25

- Initial alpha release.

Notes
-----

`Leica Microsystems GmbH <https://www.leica.com/>`_ is a manufacturer of
microscopes and scientific instruments for the analysis of micro and
nanostructures.

This library is in its early stages of development. It is not feature-complete.
Large, backwards-incompatible changes may occur between revisions.

Specifically, the following features are currently not supported:
related Leica file formats (XLEF, XLLF, LIFEXT), image mosaics and
pyramids, partial image reads, reading non-image data like FLIM/TCSPC,
heterogeneous channel data types, discontiguous storage, and bit increments.

The library has been tested with a limited number of version 2 files only.

The Leica Image File format is documented at:

- Leica Image File Formats - LIF, XLEF, XLLF, LOF. Version 3.2.
  Leica Microsystems GmbH. 21 September 2016.
- Annotations to Leica Image File Formats for LAS X Version 3.x. Version 1.4.
  Leica Microsystems GmbH. 24 August 2016.
- TSC SP8 FALCON File Format Description. LAS X Version 3.5.0.

Other implementations for reading Leica LIF files are
`readlif <https://github.com/Arcadia-Science/readlif>`_ and
`Bio-Formats <https://github.com/ome/bioformats>`_ .

Examples
--------

Read a FLIM lifetime image and metadata from a LIF file:

>>> with LifFile('tests/data/FLIM.lif') as lif:
...     for image in lif.series:
...         name = image.name
...     image = lif.series['Fast Flim']
...     assert image.shape == (1024, 1024)
...     assert image.dims == ('Y', 'X')
...     lifetimes = image.asxarray()
...
>>> lifetimes
<xarray.DataArray 'Fast Flim' (Y: 1024, X: 1024)> Size: 2MB
array([[...]],
      shape=(1024, 1024), dtype=float16)
    Coordinates:
      * Y        (Y) float64... 0.0005564
      * X        (X) float64... 0.0005564
Attributes...
    path:           FLIM_testdata.lif/sample1_slice1/FLIM Compressed/Fast Flim
    F16:            {'Name': 'F16',...
    TileScanInfo:   {'Tile': {'FieldX': 0,...
    ViewerScaling:  {'ChannelScalingInfo': {...

View the image and metadata in a LIF file from the console::

    $ python -m liffile tests/data/FLIM.lif

"""

from __future__ import annotations

__version__ = '2025.2.2'

__all__ = [
    '__version__',
    'imread',
    'logger',
    'LifFile',
    'LifFileError',
    'LifImageABC',
    'LifImage',
    'LifFlimImage',
    'LifImageSeries',
    'LifMemoryBlock',
    'FILE_EXTENSIONS',
]

import logging
import math
import os
import re
import struct
import sys
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import cached_property
from typing import TYPE_CHECKING, final, overload
from xml.etree import ElementTree

if TYPE_CHECKING:
    from collections.abc import Container, Iterable, Iterator
    from typing import IO, Any, Literal

    from numpy.typing import DTypeLike, NDArray
    from xarray import DataArray

    OutputType = str | IO[bytes] | NDArray[Any] | None

import numpy


@overload
def imread(
    file: str | os.PathLike[Any] | IO[bytes],
    /,
    *,
    series: int | str = 0,
    asrgb: bool = True,
    squeeze: bool = True,
    out: OutputType = None,
    asxarray: Literal[False] = ...,
) -> NDArray[Any]: ...


@overload
def imread(
    file: str | os.PathLike[Any] | IO[bytes],
    /,
    *,
    series: int | str = 0,
    asrgb: bool = True,
    squeeze: bool = True,
    out: OutputType = None,
    asxarray: Literal[True] = ...,
) -> DataArray: ...


def imread(
    file: str | os.PathLike[Any] | IO[bytes],
    /,
    *,
    series: int | str = 0,
    squeeze: bool = True,
    out: OutputType = None,
    asxarray: bool = False,
    **kwargs: Any,
) -> NDArray[Any] | DataArray:
    """Return image from file.

    Dimensions are returned in order stored in file.

    Parameters:
        file:
            Name of Leica image file or seekable binary stream.
        series:
            Index or name of image to return.
            By default, the first image in the file is returned.
        squeeze:
            Remove dimensions of length one from images.
        out:
            Specifies where to copy image data.
            If ``None``, create a new NumPy array in main memory.
            If ``'memmap'``, directly memory-map the image data in the file.
            If a ``numpy.ndarray``, a writable, initialized array
            of compatible shape and dtype.
            If a ``file name`` or ``open file``, create a memory-mapped
            array in the specified file.
        asxarray:
            Return image data as xarray.DataArray instead of numpy.ndarray.
        **kwargs:
            Optional arguments to :py:meth:`LifImageABC.asarray`.

    Returns:
        :
            Image data as numpy array or xarray DataArray.

    """
    data: NDArray[Any] | DataArray
    with LifFile(file, squeeze=squeeze) as lif:
        image = lif.series[series]
        if asxarray:
            data = image.asxarray(out=out, **kwargs)
        else:
            data = image.asarray(out=out, **kwargs)
    return data


class LifFileError(Exception):
    """Exception to indicate invalid Leica Image File structure."""


@final
class LifFile:
    """Leica Image File.

    ``LifFile`` instances are not thread-safe. All attributes are read-only.

    ``LifFile`` instances must be closed with :py:meth:`LifFile.close`,
    which is automatically called when using the 'with' context manager.

    All properties are read-only.

    Parameters:
        file:
            Name of Leica image file or seekable binary stream.
        mode:
            File open mode if `file` is file name.
            The default is 'r'. Files are always opened in binary mode.
        squeeze:
            Remove dimensions of length one from images.

    Raises:
        LifFileError: File is not a Leica image file or is corrupted.

    """

    filename: str
    """Name of file or empty if binary stream."""

    version: int
    """File version."""

    name: str
    """Name of file from XML header."""

    uuid: str | None
    """Unique identifier of file, if any."""

    is_lof: bool
    """File has LOF format."""

    xml_element: ElementTree.Element
    """XML header root element."""

    memory_blocks: dict[str, LifMemoryBlock]
    """Object memory blocks."""

    _fh: IO[bytes]
    _close: bool  # file needs to be closed
    _squeeze: bool  # remove dimensions of length one from images
    _xml_header: tuple[int, int]  # byte offset and size of XML header

    def __init__(
        self,
        file: str | os.PathLike[Any] | IO[bytes],
        /,
        *,
        squeeze: bool = True,
        mode: Literal['r', 'r+'] | None = None,
    ) -> None:
        if isinstance(file, (str, os.PathLike)):
            if mode is None:
                mode = 'r'
            else:
                if mode[-1:] == 'b':
                    mode = mode[:-1]  # type: ignore[assignment]
                if mode not in {'r', 'r+'}:
                    raise ValueError(f'invalid mode {mode!r}')
            self.filename = os.fspath(file)
            self._close = True
            self._fh = open(self.filename, mode + 'b')
        elif hasattr(file, 'seek'):
            self.filename = ''
            self._close = False
            self._fh = file
        else:
            raise ValueError(f'cannot open file of type {type(file)}')

        self._squeeze = bool(squeeze)
        self.is_lof = False
        self.version = 0
        self.name = ''
        self.uuid = None
        self.memory_blocks = {}
        self._xml_header = (0, 0)
        # self.xml_element =

        try:
            self._init(self._fh)
        except Exception:
            self.close()
            raise

    def _init(self, fh: IO[bytes], /) -> None:
        """Initialize from open file."""
        # read binary header
        try:
            id0, size, id1, strlen = struct.unpack('<IIBI', fh.read(13))
        except Exception as exc:
            raise LifFileError('not a Leica image file') from exc
        if id0 != 0x70 or id1 != 0x2A:  # or size != 2 * strlen + 5
            raise LifFileError(
                'not a Leica image file '
                f'({id0=:02X} != 0x70 or {id1=:02X} != 0x2A)'
            )
        self._xml_header = (fh.tell(), strlen * 2)
        xml_header = fh.read(strlen * 2).decode('utf-16-le')

        self.is_lof = xml_header == 'LMS_Object_File'

        if self.is_lof:
            # read memory block
            try:
                id0, ver0, id1, ver1 = struct.unpack('<BIBI', fh.read(10))
            except Exception as exc:
                raise LifFileError('corrupted Leica object file') from exc
            if id0 != 0x2A or id1 != 0x2A:
                raise LifFileError(
                    'corrupted Leica object file '
                    f'({id0=:02X} != 0x2A or {id1=:02X} != 0x2A)'
                )
            memblock = LifMemoryBlock(fh, -1)

            # read XML header
            try:
                id0, size, id1, xmlsize = struct.unpack('<IIBI', fh.read(13))
            except Exception as exc:
                raise LifFileError('corrupted Leica object file') from exc
            if id0 != 0x70 or id1 != 0x2A or size != 2 * xmlsize + 5:
                raise LifFileError(
                    'corrupted Leica object file '
                    f'({id0=:02X} != 0x70, {id1=:02X} != 0x2A, or '
                    f'{size=} != {2 * xmlsize + 5})'
                )
            self._xml_header = (fh.tell(), xmlsize * 2)
            xml_header = fh.read(xmlsize * 2).decode('utf-16-le')

        self.xml_element = ElementTree.fromstring(xml_header)

        # TODO: some XML found in (older?) LOF files do not contain a
        # versioned <LMSDataContainerHeader> element required by the
        # LOF specification, but instead start with <Data><Image> elements.
        # For now, let those files pass without exception, albeit with
        # an empty series.

        try:
            self.version = int(self.xml_element.attrib['Version'])
        except KeyError:
            if not self.is_lof:
                raise KeyError(
                    "'Version' attribute not found in XML root element"
                )

        # add memory blocks
        if self.is_lof:
            # LOF files only contain a single memory block without id.
            # Any id would work.
            # However, try to preserve original id from XML metadata.
            try:
                memory = self.xml_element.find('./Element/Memory')
                if memory is None:
                    raise ValueError('Memory element not found in XML')
                memblock_id = memory.get('MemoryBlockID')
                if memblock_id is None:
                    raise ValueError(
                        'MemoryBlockID attribute not found in XML'
                    )
            except ValueError:
                memblock_id = 'MemBlock_0'

            memblock.id = memblock_id  # LOF memory blocks don't have id
            self.memory_blocks[memblock.id] = memblock
        else:
            while True:
                try:
                    memblock = LifMemoryBlock(fh, self.version)
                except OSError:
                    break
                self.memory_blocks[memblock.id] = memblock

        element = self.xml_element.find('./Element')
        if element is None:
            logger().warning(f'{self!r} no XML image element found')
        else:
            self.name = element.attrib.get('Name', self.name)
            self.uuid = element.attrib.get('UniqueID')

    @property
    def filehandle(self) -> IO[bytes]:
        """File handle."""
        return self._fh

    @property
    def datetime(self) -> datetime | None:
        """File creation date from XML header."""
        element = self.xml_element.find('./Element/Data/Experiment/TimeStamp')
        if element is None:
            return None
        high = int(element.attrib['HighInteger'])
        low = int(element.attrib['LowInteger'])
        sec = (((high << 32) + low) - 116444736000000000) // 10000000
        return datetime.fromtimestamp(sec, timezone.utc)

    @cached_property
    def series(self) -> LifImageSeries:
        """Image series in file."""
        return LifImageSeries(self)

    def xml_header(self) -> str:
        """Return XML object description from file."""
        self._fh.seek(self._xml_header[0])
        return self._fh.read(self._xml_header[1]).decode('utf-16-le')

    def close(self) -> None:
        """Close file handle and free resources."""
        if self._close:
            try:
                self._fh.close()
            except Exception:
                pass

    def __enter__(self) -> LifFile:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        if self.filename:
            name = os.path.basename(self.filename)
        elif hasattr(self._fh, 'name') and self._fh.name:
            name = os.path.basename(self._fh.name)
        else:
            name = self.name
        return f'<{self.__class__.__name__} {name!r}>'

    def __str__(self) -> str:
        return indent(
            repr(self),
            f'filename: {self.filename}',
            f'datetime: {self.datetime}',
            f'uuid: {self.uuid}',
            indent('series:', *(repr(image) for image in self.series)),
            indent(
                'memory_blocks:',
                *(
                    repr(memblock)
                    for memblock in self.memory_blocks.values()
                    if memblock.size > 0
                ),
            ),
        )


class LifImageABC(ABC):
    """Base class for :py:class:`LifImage` and :py:class:`LifFlimImage`.

    All properties are read-only.

    Parameters:
        parent:
            Underlying LIF file.
        xml_element:
            XML element of image.
        path:
            Path of image in image tree.

    Notes:
        LIF images may have the following dimensions in almost any order:

        - ``'H'``: TCSPC histogram
        - ``'S'``: Sample/color component
        - ``'C'``: Channel
        - ``'X'``: Width
        - ``'Y'``: Height
        - ``'Z'``: Depth
        - ``'T'``: Time
        - ``'λ'``: Emission wavelength
        - ``'A'``: Rotation
        - ``'N'``: XT slices
        - ``'Q'``: T slices
        - ``'Λ'``: Excitation wavelength
        - ``'M'``: Mosaic (``'S'`` in LAS X)
        - ``'L'``: Loop

    """

    parent: LifFile
    """Underlying LIF file."""

    xml_element: ElementTree.Element
    """XML element of image."""

    path: str
    """Path of image in image tree."""

    index: int
    """Index of image in LIF file."""

    def __init__(
        self,
        parent: LifFile,
        xml_element: ElementTree.Element,
        path: str,
        index: int,
        /,
    ) -> None:
        self.parent = parent
        self.xml_element = xml_element
        self.path = path
        self.index = index

    @property
    def is_flim(self) -> bool:
        """Image contains FLIM/TCSPC histogram."""
        return isinstance(self, LifFlimImage)

    @property
    def name(self) -> str:
        """Name of image."""
        return os.path.split(self.path)[-1]

    @property
    def uuid(self) -> str | None:
        """Unique identifier of image, if any."""
        return self.xml_element.attrib.get('UniqueID')

    @property
    @abstractmethod
    def xml_element_smd(self) -> ElementTree.Element | None:
        """SingleMoleculeDetection XML element, if any."""

    @cached_property
    @abstractmethod
    def dtype(self) -> numpy.dtype[Any]:
        """Numpy data type of image array."""

    @cached_property
    @abstractmethod
    def sizes(self) -> dict[str, int]:
        """Map dimension names to lengths."""

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape of image."""
        return tuple(self.sizes.values())

    @property
    def dims(self) -> tuple[str, ...]:
        """Character codes of dimensions in image."""
        return tuple(self.sizes.keys())

    @property
    def ndim(self) -> int:
        """Number of image dimensions."""
        return len(self.sizes)

    @property
    def nbytes(self) -> int:
        """Number of bytes consumed by image."""
        size = 1
        for i in self.sizes.values():
            size *= int(i)
        return size * self.dtype.itemsize

    @property
    def size(self) -> int:
        """Number of elements in image."""
        size = 1
        for i in self.sizes.values():
            size *= int(i)
        return size

    @property
    def itemsize(self) -> int:
        """Length of one array element in bytes."""
        return self.dtype.itemsize

    @cached_property
    @abstractmethod
    def coords(self) -> dict[str, NDArray[Any]]:
        """Mapping of image dimension names to coordinate variables."""

    @cached_property
    @abstractmethod
    def attrs(self) -> dict[str, Any]:
        """Image metadata from XML elements."""

    @cached_property
    def memory_block(self) -> LifMemoryBlock:
        """Memory block containing image data."""
        if self.parent.is_lof:
            # LOF files contain one memory block
            return self.parent.memory_blocks[
                tuple(self.parent.memory_blocks.keys())[0]
            ]
        memory = self.xml_element.find('./Memory')
        if memory is None:
            raise IndexError('Memory element not found in XML')
        mbid = memory.get('MemoryBlockID')
        if mbid is None:
            raise IndexError('MemoryBlockID attribute not found in XML')
        return self.parent.memory_blocks[mbid]

    @property
    def timestamps(self) -> NDArray[numpy.datetime64]:
        """Return time stamps of frames from TimeStampList XML element."""
        return numpy.asarray([], dtype=numpy.datetime64)

    # @abstractmethod
    # def frames(self) -> Iterator[NDArray[Any]]:
    #     """Return iterator over frames in image."""

    @abstractmethod
    def asarray(
        self,
        *,
        out: OutputType = None,
    ) -> NDArray[Any]:
        """Return image data as array.

        Dimensions are returned in order stored in file.

        Parameters:
            out:
                Specifies where to copy image data.
                If ``None``, create a new NumPy array in main memory.
                If ``'memmap'``, directly memory-map the image data in the
                file if possible; else create a memory-mapped array in a
                temporary file.
                If a ``numpy.ndarray``, a writable, initialized array
                of :py:attr:`shape` and :py:attr:`dtype`.
                If a ``file name`` or ``open file``, create a
                memory-mapped array in the specified file.
            **kwargs:
                Optional arguments.

        Returns:
            :
                Image data as numpy array.

        """

    def asxarray(self, **kwargs: Any) -> DataArray:
        """Return image data as xarray.

        Dimensions are returned in order stored in file.

        Parameters:
            **kwargs: Optional arguments to :py:meth:`asarray`.

        Returns:
            :
                Image data and select metadata as xarray DataArray.

        """
        from xarray import DataArray

        return DataArray(
            self.asarray(**kwargs),
            coords=self.coords,
            dims=self.dims,
            name=self.name,
            attrs=self.attrs,
        )

    def __repr__(self) -> str:
        # TODO: make columns configurable?
        # such that it can be set to os.get_terminal_size().columns
        columns = 115
        name = self.__class__.__name__
        index = self.index
        path = self.path
        dtype = self.dtype
        sizes = ', '.join(f'{k}: {v}' for k, v in self.sizes.items())
        r = f'<{name} {index} {path!r} ({sizes}) {dtype}>'
        if len(r) > columns + 2:
            path = '… ' + self.path[len(r) - columns :]
            r = f'<{name} {index} {path!r} ({sizes}) {dtype}>'
        return r

    def __str__(self) -> str:
        return indent(
            repr(self),
            *(
                f'{name}: {getattr(self, name)!r}'[:160]
                for name in dir(self)
                if not (name.startswith('_') or callable(getattr(self, name)))
            ),
        )


@final
class LifImage(LifImageABC):
    """Regular image.

    Defined by XML Element with Data/Image child.

    """

    @property
    def xml_element_smd(self) -> ElementTree.Element | None:
        uuid = self.uuid
        return self.parent.xml_element.find(
            f'.//Element[@UniqueID="{uuid}"]../../Data/SingleMoleculeDetection'
        )

    @cached_property
    def _dimensions(self) -> tuple[LifDimension, ...]:
        """Dimension properties from DimensionDescription XML element."""
        dimensions = []
        labels = set()
        for i, dim in enumerate(
            self.xml_element.findall(
                './Data/Image/ImageDescription/Dimensions/DimensionDescription'
            )
        ):
            dim_id = int(dim.attrib['DimID'])
            label = DIMENSION_ID.get(dim_id, 'Q')
            if label in labels:
                logger().warning(f'duplicate dimension {label!r}')
                label = f'{label}{i}'
            labels.add(label)
            dimensions.append(
                LifDimension(
                    label,
                    dim_id,
                    int(dim.attrib['NumberOfElements']),
                    float(dim.attrib['Origin']),
                    float(dim.attrib['Length']),
                    dim.attrib['Unit'],
                    int(dim.attrib['BytesInc']),
                    int(dim.attrib['BitInc']),
                )
            )
        return tuple(
            sorted(dimensions, key=lambda x: x.bytes_inc, reverse=True)
        )

    @cached_property
    def _channels(self) -> tuple[LifChannel, ...]:
        """Channel properties from ChannelDescription XML element."""
        channels = []
        for channel in self.xml_element.findall(
            './Data/Image/ImageDescription/Channels/ChannelDescription'
        ):
            data_type = int(channel.attrib['DataType'])
            resolution = int(channel.attrib['Resolution'])

            if data_type == 0:
                dtype = 'u'
            elif data_type == 1:
                dtype = 'f'
            else:
                raise ValueError(f'invalid {data_type=}')

            if 0 < resolution <= 8:
                itemsize = 1
                if dtype == 'f':
                    raise ValueError(f'invalid dtype {dtype}{itemsize}')
            elif resolution <= 16:
                itemsize = 2
            elif resolution <= 32:
                itemsize = 4
            elif resolution <= 64:
                itemsize = 8
            else:
                raise ValueError(f'invalid {resolution=}')

            channels.append(
                LifChannel(
                    numpy.dtype(f'<{dtype}{itemsize}'),
                    data_type,
                    int(channel.attrib['ChannelTag']),
                    resolution,
                    channel.attrib['NameOfMeasuredQuantity'],
                    float(channel.attrib['Min']),
                    float(channel.attrib['Max']),
                    channel.attrib['Unit'],
                    channel.attrib['LUTName'],
                    bool(channel.attrib['IsLUTInverted']),
                    int(channel.attrib['BytesInc']),
                    int(channel.attrib['BitInc']),
                )
            )

        return tuple(
            sorted(channels, key=lambda x: x.bytes_inc, reverse=False)
        )

    @cached_property
    def dtype(self) -> numpy.dtype[Any]:
        channels = self._channels
        dtype = channels[0].dtype

        if len(channels) > 1 and any(dtype != c.dtype for c in channels):
            raise ValueError(
                'heterogeneous channel data types not supported. '
                'Please share the file at https://github.com/cgohlke/liffile'
            )

        return dtype

    @cached_property
    def sizes(self) -> dict[str, int]:
        squeeze = self.parent._squeeze
        channels = self._channels
        nchannels = len(channels)
        if nchannels <= 1:
            return {
                dim.label: dim.number_elements
                for dim in self._dimensions
                if not squeeze or dim.number_elements > 1
            }

        # insert channels where other dimensions are discontiguous
        # TODO: verify with channel BytesInc
        sizes = {}
        stride = self.dtype.itemsize
        ch = 0
        for i, dim in enumerate(reversed(self._dimensions)):
            if squeeze and dim.number_elements < 2:
                continue
            if stride != dim.bytes_inc:
                assert dim.bytes_inc % stride == 0
                size = dim.bytes_inc // stride
                ax = 'S' if i == 0 else 'C' if 'C' not in sizes else f'C{ch}'
                if ax != 'S':
                    ch += 1
                sizes[ax] = size
                assert nchannels % size == 0
                nchannels //= size
            sizes[dim.label] = dim.number_elements
            stride = dim.number_elements * dim.bytes_inc
        if nchannels > 1:
            ax = 'C' if 'C' not in sizes else f'C{ch}'
            sizes[ax] = nchannels

        return dict(reversed(list(sizes.items())))

    @cached_property
    def coords(self) -> dict[str, NDArray[Any]]:
        # TODO: add channel names. Channels may be in several dimensions
        squeeze = self.parent._squeeze
        coords = {}
        for dim in self._dimensions:
            if squeeze and dim.number_elements == 1:
                continue
            if dim.length == 0 and dim.number_elements > 1:
                continue
            coords[dim.label] = numpy.linspace(
                dim.origin,
                dim.origin + dim.length,
                dim.number_elements,
                endpoint=True,
            )
        return coords

    @cached_property
    def attrs(self) -> dict[str, Any]:
        if self.parent.is_lof:
            path = self.path
        else:
            path = self.parent.name + '/' + self.path
        attrs = {'path': path}
        attrs.update(
            (attach.attrib['Name'], xml2dict(attach)['Attachment'])
            for attach in self.xml_element.findall('./Data/Image/Attachment')
        )
        return attrs

    @property
    def timestamps(self) -> NDArray[numpy.datetime64]:
        timestamp = self.xml_element.find('./Data/Image/TimeStampList')
        if timestamp is None:
            return numpy.asarray([], dtype=numpy.datetime64)
        timestamps: Any
        if timestamp.find('./TimeStamp') is not None:
            # LAS < 3.1
            text = ElementTree.tostring(timestamp).decode()
            high_integers = ' '.join(re.findall(r'HighInteger="(\d+)"', text))
            low_integers = ' '.join(re.findall(r'LowInteger="(\d+)"', text))
            timestamps = numpy.fromstring(
                high_integers, dtype=numpy.uint64, sep=' '
            )
            timestamps <<= 32
            timestamps += numpy.fromstring(
                low_integers, dtype=numpy.uint32, sep=' '
            )
        elif timestamp.text is not None:
            # LAS >= 3.1
            timestamps = numpy.fromiter(
                (int(x, 16) for x in timestamp.text.split()),
                dtype=numpy.uint64,
            )
        else:
            return numpy.asarray([], dtype=numpy.datetime64)
        # FILETIME to POSIX
        timestamps -= 116444736000000000
        timestamps //= 10000
        return timestamps.astype(  # type: ignore[no-any-return]
            'datetime64[ms]'
        )

    def asarray(
        self,
        *,
        asrgb: bool = True,
        mode: str = 'r',
        out: OutputType = None,
    ) -> NDArray[Any]:
        """Return image data as array.

        Dimensions are returned in order stored in file.

        Parameters:
            asrgb:
                Return RGB samples in RGB order.
                If true, the returned array might not be contiguous.
            mode:
                Memmap file open mode. The default is read-only.
            out:
                Specifies where to copy image data.
                If ``None``, create a new NumPy array in main memory.
                If ``'memmap'``, directly memory-map the image data in the
                file if possible; else create a memory-mapped array in a
                temporary file.
                If a ``numpy.ndarray``, a writable, initialized array
                of :py:attr:`shape` and :py:attr:`dtype`.
                If a ``file name`` or ``open file``, create a
                memory-mapped array in the specified file.

        Returns:
            :
                Image data as numpy array.

        """
        data = self.memory_block.read_array(
            self.parent.filehandle, self.shape, self.dtype, mode=mode, out=out
        )
        if (
            asrgb
            and self.sizes.get('S', 0) == 3
            and self._channels[0].channel_tag == 3  # blue
            and self._channels[1].channel_tag == 2  # green
        ):
            data = data[..., ::-1]
        return data


@final
class LifFlimImage(LifImageABC):
    """FLIM/TCSPC histogram image.

    Defined by XML Element with Data/SingleMoleculeDetection child.

    """

    @property
    def xml_element_smd(self) -> ElementTree.Element | None:
        return self.xml_element

    @cached_property
    def dtype(self) -> numpy.dtype[Any]:
        return numpy.dtype(numpy.uint16)

    @cached_property
    def sizes(self) -> dict[str, int]:
        sizes = {'H': self.number_bins_in_period}

        dims = self.xml_element.find(
            './Data/SingleMoleculeDetection/Dataset/RawData/Dimensions'
        )
        if dims is None:
            raise ValueError('Dimensions element not found in XML')

        for dimid, size in zip(
            dims.findall('Dimension/DimensionIdentifier'),
            dims.findall('Dimension/Size'),
        ):
            if dimid.text is None or size.text is None or int(size.text) <= 1:
                continue
            name = {'M': 'A', 'S': 'M'}.get(dimid.text, dimid.text)
            sizes[name] = int(size.text)

        return dict(reversed(list(sizes.items())))

    @cached_property
    def coords(self) -> dict[str, NDArray[Any]]:
        attrs = self.attrs['RawData']
        sizes = self.sizes
        coords = {}
        for ax in 'ZYX':
            if ax in sizes:
                coords[ax] = numpy.linspace(
                    0.0,
                    attrs['VoxelSize' + ax] * sizes[ax],
                    sizes[ax],
                    endpoint=False,
                )
        if 'H' in sizes:
            coords['H'] = numpy.linspace(
                0,
                self.number_bins_in_period * attrs['ClockPeriod'],
                self.number_bins_in_period,
                endpoint=False,
            )
        return coords

    @cached_property
    def attrs(self) -> dict[str, Any]:
        rawdata = self.xml_element.find(
            './Data/SingleMoleculeDetection/Dataset/RawData'
        )
        if rawdata is None:
            raise ValueError('RawData element not found in XML')
        attrs = xml2dict(rawdata, exclude={'Dimensions', 'Channels'})
        return {
            'path': self.parent.name + '/' + self.path,
            'RawData': attrs['RawData'],
        }

    @property
    def global_resolution(self) -> float:
        """Resolution of time tags in s."""
        return float(1.0 / self.attrs['RawData']['LaserPulseFrequency'])

    @property
    def tcspc_resolution(self) -> float:
        """Resolution of TCSPC in s."""
        return float(self.attrs['RawData']['ClockPeriod'])

    @property
    def number_bins_in_period(self) -> int:
        """Delay time in one period."""
        attrs = self.attrs['RawData']
        frequency = attrs['LaserPulseFrequency']
        clock_period = attrs['ClockPeriod']
        return max(1, int(math.floor(1.0 / frequency / clock_period)))

    @property
    def pixel_time(self) -> float:
        """Time per pixel in s."""
        return float(self.attrs['RawData']['PixelTime'])

    @property
    def frequency(self) -> float:
        """Repetition frequency in MHz."""
        return float(1e-6 * self.attrs['RawData']['LaserPulseFrequency'])

    @property
    def is_bidirectional(self) -> bool:
        """Bidirectional scan mode."""
        return bool(self.attrs['RawData']['BiDirectional'])

    @property
    def is_sinusoidal(self) -> bool:
        """Sinusoidal scan mode."""
        return bool(self.attrs['RawData']['SinusCorrection'])

    def asarray(
        self,
        *,
        dtype: DTypeLike | None = None,
        frame: int | None = None,
        channel: int | None = None,
        dtime: int | None = None,
        out: OutputType = None,
    ) -> NDArray[Any]:
        """Return image data as array.

        Dimensions are returned in order stored in file.

        Parameters:
            dtype:
                Unsigned integer type of image histogram array.
                The default is ``uint16``. Increase the bit depth to avoid
                overflows when integrating.
            frame:
                If < 0, integrate time axis, else return specified frame.
            channel:
                If < 0, integrate channel axis, else return specified channel.
            dtime:
                Specifies number of bins in image histogram.
                If 0, return :py:attr:`number_bins_in_period` bins.
                If < 0, integrate delay time axis.
                If > 0, return up to specified bin.
            out:
                Specifies where to copy image data.
                If ``None``, create a new NumPy array in main memory.
                If ``'memmap'``, create a memory-mapped array in a
                temporary file.
                If a ``numpy.ndarray``, a writable, initialized array
                of :py:attr:`shape` and :py:attr:`dtype`.
                If a ``file name`` or ``open file``, create a
                memory-mapped array in the specified file.

        Returns:
            :
                Image data as numpy array.

        """
        format = self.attrs['RawData']['Format']
        raise NotImplementedError(f'{format=!r} is patent-pending')


@final
class LifImageSeries(Sequence[LifImageABC]):
    """Sequence of images in LIF file."""

    __slots__ = ('_parent', '_images')

    _parent: LifFile
    _images: dict[str, LifImageABC]

    def __init__(self, parent: LifFile) -> None:
        self._parent = parent
        self._images = {}
        for index, (path, element) in enumerate(
            LifImageSeries._image_iter(parent.xml_element)
        ):
            image: LifImageABC
            path = path.split('/', 1)[-1]
            if element.find('./Data/SingleMoleculeDetection') is None:
                image = LifImage(parent, element, path, index)
            else:
                image = LifFlimImage(parent, element, path, index)
            self._images[path] = image

    @staticmethod
    def _image_iter(
        xml_element: ElementTree.Element,
        base_path: str = '',
        /,
    ) -> Iterator[tuple[str, ElementTree.Element]]:
        """Return iterator of image paths and XML elements."""
        elements = xml_element.findall('./Children/Element')
        if len(elements) < 1:
            elements = xml_element.findall('./Element')
        for element in elements:
            name = element.attrib['Name']
            if base_path == '' or base_path.endswith(name):
                path = name
            else:
                path = f'{base_path}/{name}'
            image = element.find('./Data/Image')
            if image is not None:
                yield path, element
            else:
                # FLIM/TCSPC
                image = element.find(
                    './Data/SingleMoleculeDetection[@IsImage="true"]'
                )
                if image is not None:
                    yield path, element
            if element.find('./Children/Element/Data') is not None:
                # sub images
                yield from LifImageSeries._image_iter(element, path)

    def findall(
        self, key: str, /, *, flags: int = re.IGNORECASE
    ) -> tuple[LifImageABC, ...]:
        """Return all images with matching path pattern.

        Parameters:
            key:
                Regular expression pattern to match LifImage.path.
            flags:
                Regular expression flags.

        """
        pattern = re.compile(key, flags=flags)
        images = []
        for path, image in self._images.items():
            if pattern.search(path) is not None:
                images.append(image)
        return tuple(images)

    def paths(self) -> Iterator[str]:
        """Return iterator over image paths."""
        return iter(self._images.keys())

    def __getitem__(  # type: ignore[override]
        self,
        key: int | str,
        /,
    ) -> LifImageABC:
        """Return image at index or first image with matching path."""
        if isinstance(key, int):
            return self._images[tuple(self._images.keys())[key]]
        if key in self._images:
            return self._images[key]
        pattern = re.compile(key, flags=re.IGNORECASE)
        for path, image in self._images.items():
            if pattern.search(path) is not None:
                return image
        raise KeyError(key)

    def __len__(self) -> int:
        return len(self._images)

    def __iter__(self) -> Iterator[LifImageABC]:
        return iter(self._images.values())

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} len={len(self._images)}>'

    def __str__(self) -> str:
        return indent(
            repr(self), *(repr(image) for image in self._images.values())
        )


@final
class LifMemoryBlock:
    """Object memory block.

    Parameters:
        fh: File handle.
        version: LIF file version.

    """

    __slots__ = ('id', 'offset', 'size')

    id: str
    """Identity of memory block."""

    offset: int
    """Byte offset of memory block in file."""

    size: int
    """Size of memory block in bytes."""

    def __init__(
        self,
        fh: IO[bytes],
        version: int,
        /,
    ):
        if version == -1:
            # LOF
            fmtstr = '<BQ'
        elif version == 1:
            fmtstr = '<IIBIBI'
        elif version == 2:
            fmtstr = '<IIBQBI'
        else:
            raise ValueError(f'invalid memory block {version=}')

        size = struct.calcsize(fmtstr)
        buffer = fh.read(size)
        if len(buffer) != size:
            raise OSError

        if version < 0:
            # LOF
            self.id = 'MemBlock_0'  # updated in LifFile._init
            id0, self.size = struct.unpack(fmtstr, buffer)
            if id0 != 0x2A:
                raise LifFileError(
                    f'corrupted LOF memory block ({id0=:02X} != 0x2A)'
                )
        else:
            id0, _, id1, size1, id2, strlen = struct.unpack(fmtstr, buffer)
            if id0 != 0x70 or id1 != 0x2A or id2 != 0x2A:
                raise LifFileError(
                    f'corrupted LIF memory block ({id0=:02X} != 0x70, '
                    f'{id1=:02X} != 0x2A, or {id2=:02X} != 0x2A)'
                )

            buffer = fh.read(strlen * 2)
            if len(buffer) != strlen * 2:
                raise OSError
            self.id = buffer.decode('utf-16-le')
            self.size = size1

        self.offset = fh.tell()
        fh.seek(self.offset + self.size)
        if fh.tell() - self.offset != self.size:
            raise OSError

    def read(self, fh: IO[bytes], /) -> bytes:
        """Return memory block from file."""
        fh.seek(self.offset)
        buffer = fh.read(self.size)
        if len(buffer) != self.size:
            raise OSError(f'read {len(buffer)} bytes, expected {self.size}')
        return buffer

    def read_array(
        self,
        fh: IO[bytes],
        /,
        shape: tuple[int, ...],
        dtype: DTypeLike,
        *,
        mode: str = 'r',
        out: OutputType = None,
    ) -> NDArray[Any]:
        """Return NumPy array from file.

        Parameters:
            fh:
                Open file handle to read from.
            shape:
                Shape of array to read.
            dtype:
                Data type of array to read.
            mode:
                Memmap file open mode. The default is read-only.
            out:
                Specifies where to copy image data.
                If ``None``, create a new NumPy array in main memory.
                If ``'memmap'``, directly memory-map the image data in the
                file if possible; else create a memory-mapped array in a
                temporary file.
                If a ``numpy.ndarray``, a writable, initialized array
                of `shape` and `dtype`.
                If a ``file name`` or ``open file``, create a
                memory-mapped array in the specified file.

        """
        dtype = numpy.dtype(dtype)
        nbytes = product(shape) * dtype.itemsize
        if nbytes > self.size:
            raise ValueError(
                f'array size={nbytes} > memory block size={self.size}'
            )
        if nbytes != self.size:
            logger().warning(f'{self!r} != array size={nbytes}')

        if isinstance(out, str) and out == 'memmap':
            return numpy.memmap(  # type: ignore[no-any-return]
                fh,  # type: ignore[call-overload]
                dtype=dtype,
                mode=mode,
                offset=self.offset,
                shape=shape,
                order='C',
            )

        data = create_output(out, shape, dtype)
        if data.nbytes != nbytes:
            raise ValueError('size mismatch')

        fh.seek(self.offset)
        try:
            n = fh.readinto(data)  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            data[:] = numpy.frombuffer(fh.read(nbytes), dtype).reshape(
                data.shape
            )
            n = nbytes

        if n != nbytes:
            raise ValueError(f'failed to read {nbytes} bytes, got {n}')

        if out is not None:
            if hasattr(out, 'flush'):
                out.flush()

        return data

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} {self.id!r} '
            f'offset={self.offset} size={self.size}>'
        )


@dataclass
class LifChannel:
    """Attributes of Image/ChannelDescription XML element."""

    dtype: numpy.dtype[Any]
    """Numpy dtype from data_type and resolution."""
    data_type: int
    """Data type, integer (0) or float (1)."""
    channel_tag: int
    """Gray (0), Red (1), Green (2), or Blue (3)."""
    resolution: float
    """Bits per pixel."""
    name_of_measured_quantity: str
    """Name of measured quantity."""
    min: float
    """Physical value of lowest gray value."""
    max: float
    """Physical value of highest gray value."""
    unit: str
    """Physical unit."""
    lut_name: str
    """Name of Look Up Table."""
    is_lut_inverted: bool
    """Look Up Table is inverted."""
    bytes_inc: int
    """Distance from the first channel in bytes."""
    bit_inc: int
    """Bit distance."""


@dataclass
class LifDimension:
    """Attributes of Image/DimensionDescription XML element."""

    label: str
    """Label of dimension."""
    dim_id: int
    """Type of dimension."""
    number_elements: int
    """Number of elements."""
    origin: float
    """Physical position of first element."""
    length: float
    """Physical length from first to last element."""
    unit: str
    """Physical unit."""
    bytes_inc: int
    """Distance from one element to the next."""
    bit_inc: int
    """Bit distance."""


@dataclass
class LifRawData:
    """Attributes of SingleMoleculeDetection/Dataset/RawData XML element."""

    format: str
    """Raw data dormat."""
    voxel_size_x: float
    """Spatial dimension size in m."""
    voxel_size_y: float
    """Spatial dimension size in m."""
    voxel_size_z: float
    """Spatial dimension size in m."""
    clock_period: float
    """Base clock in s."""
    syncronization_marker_period: float
    """Clock period of the FCS counter in s."""
    frame_repetitions_marked: bool
    """Frames completed when number photons detected."""
    pixel_time: str
    """Pixel dwell time in s."""
    bi_directional: bool
    """Bi-directional scan."""
    sequential_mode: bool
    """Look Up Table is inverted."""


DIMENSION_ID = {
    # 0: 'C',  # sample, channel
    1: 'X',
    2: 'Y',
    3: 'Z',
    4: 'T',
    5: 'λ',  # emission wavelength
    6: 'A',  # rotation ?
    7: 'N',  # XT slices
    8: 'Q',  # T slices ?
    9: 'Λ',  # excitation wavelength
    10: 'M',  # mosaic position. 'S' in LAS X
    11: 'L',  # loop
}
"""Map dimension id to character code."""

CHANNEL_TAG = {
    0: 'Gray',
    1: 'Red',
    2: 'Green',
    3: 'Blue',
}
"""Map channel tag to name."""

FILE_EXTENSIONS = {
    '.lif': LifFile,
    '.lof': LifFile,
    # '.xlif': XlifFile,
    # '.xlef': XlefFile,
    # '.xllf': XllfFile,
    # '.lifext': LifextFile,
    # '.xlcf': XlcfFile,
}
"""Supported file extensions of Leica image files."""


def create_output(
    out: OutputType,
    /,
    shape: tuple[int, ...],
    dtype: DTypeLike,
) -> NDArray[Any] | numpy.memmap[Any, Any]:
    """Return NumPy array where images of shape and dtype can be copied."""
    if out is None:
        return numpy.zeros(shape, dtype)
    if isinstance(out, numpy.ndarray):
        out.shape = shape
        return out
    if isinstance(out, str) and out[:6] == 'memmap':
        import tempfile

        tempdir = out[7:] if len(out) > 7 else None
        with tempfile.NamedTemporaryFile(dir=tempdir, suffix='.memmap') as fh:
            return numpy.memmap(fh, shape=shape, dtype=dtype, mode='w+')
    return numpy.memmap(out, shape=shape, dtype=dtype, mode='w+')


def xml2dict(
    xml_element: ElementTree.Element,
    /,
    *,
    sanitize: bool = True,
    prefix: tuple[str, str] | None = None,
    exclude: Container[str] | None = None,
    sep: str = ',',
) -> dict[str, Any]:
    """Return XML as dictionary.

    Parameters:
        xml: XML data to convert.
        sanitize: Remove prefix from from etree Element.
        prefix: Prefixes for dictionary keys.
        exclude: Ignore element tags.
        sep: Sequence separator.

    """
    at, tx = prefix if prefix else ('', '')
    exclude = set() if exclude is None else exclude

    def astype(value: Any, /) -> Any:
        # return string value as int, float, bool, tuple, or unchanged
        if not isinstance(value, str):
            return value
        if sep and sep in value:
            # sequence of numbers?
            values = []
            for val in value.split(sep):
                v = astype(val)
                if isinstance(v, str):
                    return value
                values.append(v)
            return tuple(values)
        for t in (int, float, asbool):
            try:
                return t(value)
            except (TypeError, ValueError):
                pass
        return value

    def etree2dict(t: ElementTree.Element, /) -> dict[str, Any] | None:
        # adapted from https://stackoverflow.com/a/10077069/453463
        key = t.tag
        if sanitize:
            key = key.rsplit('}', 1)[-1]
        if key in exclude:
            return None
        d: dict[str, Any] = {key: {} if t.attrib else None}
        children = list(t)
        if children:
            dd = defaultdict(list)
            for dc in map(etree2dict, children):
                if dc is not None:
                    for k, v in dc.items():
                        dd[k].append(astype(v))
            d = {
                key: {
                    k: astype(v[0]) if len(v) == 1 else astype(v)
                    for k, v in dd.items()
                }
            }
        if t.attrib:
            d[key].update((at + k, astype(v)) for k, v in t.attrib.items())
        if t.text:
            text = t.text.strip()
            if children or t.attrib:
                if text:
                    d[key][tx + 'value'] = astype(text)
            else:
                d[key] = astype(text)
        return d

    result = etree2dict(xml_element)
    return {} if result is None else result


def asbool(
    value: str,
    /,
    true: Sequence[str] | None = None,
    false: Sequence[str] | None = None,
) -> bool | bytes:
    """Return string as bool if possible, else raise TypeError.

    >>> asbool('ON', ['on'], ['off'])
    True

    """
    value = value.strip().lower()
    if true is None:
        if value == 'true':
            return True
    elif value in true:
        return True
    if false is None:
        if value == 'false':
            return False
    elif value in false:
        return False
    raise TypeError


def indent(*args: Any) -> str:
    """Return joined string representations of objects with indented lines."""
    text = "\n".join(str(arg) for arg in args)
    return "\n".join(
        ("  " + line if line else line) for line in text.splitlines() if line
    )[2:]


def product(iterable: Iterable[int], /) -> int:
    """Return product of integers."""
    prod = 1
    for i in iterable:
        prod *= int(i)
    return prod


def logger() -> logging.Logger:
    """Return logging.getLogger('liffile')."""
    return logging.getLogger(__name__.replace('liffile.liffile', 'liffile'))


def askopenfilename(**kwargs: Any) -> str:
    """Return file name(s) from Tkinter's file open dialog."""
    from tkinter import Tk, filedialog

    root = Tk()
    root.withdraw()
    root.update()
    filenames = filedialog.askopenfilename(**kwargs)
    root.destroy()
    return filenames


def main(argv: list[str] | None = None) -> int:
    """Command line usage main function.

    Preview image and metadata in specified files or all files in directory.

    ``python -m liffile file_or_directory``

    """
    from glob import glob

    imshow: Any
    try:
        from tifffile import imshow
    except ImportError:
        imshow = None

    xarray: Any
    try:
        import xarray
    except ImportError:
        xarray = None

    if argv is None:
        argv = sys.argv

    filter = False
    if len(argv) == 1:
        path = askopenfilename(
            title='Select a TIFF file',
            filetypes=[
                (f'{ext.upper()} files', f'*{ext}') for ext in FILE_EXTENSIONS
            ]
            + [('All files', '*')],
        )
        files = [path] if path else []
    elif '*' in argv[1]:
        files = glob(argv[1])
    elif os.path.isdir(argv[1]):
        files = glob(f'{argv[1]}/*.l?f')
        filter = True
    else:
        files = argv[1:]

    for fname in files:
        if (
            filter
            and os.path.splitext(fname)[-1].lower() not in FILE_EXTENSIONS
        ):
            continue
        try:
            with LifFile(fname) as lif:
                print(lif)
                print()
                if imshow is None:
                    continue
                for i, image in enumerate(lif.series):
                    if image.is_flim:
                        continue
                    im: Any
                    if xarray is not None:
                        im = image.asxarray()
                        data = im.data
                    else:
                        im = image.asarray()
                        data = im
                    print(im)
                    print()
                    if im.ndim < 2:
                        continue
                    pm = 'RGB' if image.dims[-1] == 'S' else 'MINISBLACK'
                    try:
                        imshow(
                            data,
                            title=repr(image),
                            show=i == len(lif.series) - 1,
                            photometric=pm,
                            interpolation='None',
                        )
                    except Exception as exc:
                        print(fname, exc)
        except Exception:
            import traceback

            print('Failed to read', fname)
            traceback.print_exc()
            print()
            continue

    return 0


if __name__ == '__main__':
    sys.exit(main())
