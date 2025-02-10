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

"""Read Leica image files (LIF, LOF, XLIF, XLCF, XLEF, and LIFEXT).

Liffile is a Python library to read image and metadata from Leica image files:
LIF (Leica Image File), LOF (Leica Object File), XLIF (XML Image File),
XLCF (XML Collection File), XLEF (XML Experiment File), and LIFEXT (Leica
Image File Extension).

These files are written by LAS X software to store collections of images
and metadata from microscopy experiments.

:Author: `Christoph Gohlke <https://www.cgohlke.com>`_
:License: BSD 3-Clause
:Version: 2025.2.10
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

- `CPython <https://www.python.org>`_ 3.10.11, 3.11.9, 3.12.9, 3.13.2 64-bit
- `NumPy <https://pypi.org/project/numpy>`_ 2.2.2
- `Imagecodecs <https://pypi.org/project/imagecodecs>`_ 2024.12.30
  (required for decoding TIFF, JPEG, PNG, and BMP)
- `Xarray <https://pypi.org/project/xarray>`_ 2025.1.2 (recommended)
- `Matplotlib <https://pypi.org/project/matplotlib/>`_ 3.10.0 (optional)
- `Tifffile <https://pypi.org/project/tifffile/>`_ 2025.1.10 (optional)

Revisions
---------

2025.2.10

- Support case-sensitive file systems.
- Support OMETiffBlock, AiviaTiffBlock, and other memory blocks.
- Remove LifImageSeries.items and paths methods (breaking).
- Deprecate LifImage.xml_element_smd.
- Fix LifImage.parent_image and child_images properties for XML files.
- Work around reading float16 blocks from uint16 OME-TIFF files.

2025.2.8

- Support LIFEXT files.
- Remove asrgb parameter from LifImage.asarray (breaking).
- Do not apply BGR correction when using memory block frames.
- Avoid copying single frame to output array.
- Add LifImage.parent_image and child_images properties.
- Add LifImageSeries.find method.

2025.2.6

- Support XLEF and XLCF files.
- Rename LifFile.series property to images (breaking).
- Rename imread series argument to image (breaking).
- Remove LifImage.index property (breaking).
- Add parent and children properties to LifFile.
- Improve detection of XML codecs.
- Do not keep XML files open.

2025.2.5

- Support XLIF files.
- Revise LifMemoryBlock (breaking).
- Replace LifImage.is_lof property with format (breaking).
- Require imagecodecs for decoding TIF, JPEG, PNG, and BMP frames.

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
XLLF formats, image mosaics and pyramids, partial image reads,
reading non-image data like FLIM/TCSPC, heterogeneous channel data types,
discontiguous storage, and bit increments.

The library has been tested with a limited number of version 2 files only.

The Leica image file formats are documented at:

- Leica Image File Formats - LIF, XLEF, XLLF, LOF. Version 3.2.
  Leica Microsystems GmbH. 21 September 2016.
- Annotations to Leica Image File Formats for LAS X Version 3.x. Version 1.4.
  Leica Microsystems GmbH. 24 August 2016.
- TSC SP8 FALCON File Format Description. LAS X Version 3.5.0.

Other implementations for reading Leica image files are
`readlif <https://github.com/Arcadia-Science/readlif>`_ and
`Bio-Formats <https://github.com/ome/bioformats>`_ .

Examples
--------

Read a FLIM lifetime image and metadata from a LIF file:

>>> with LifFile('tests/data/FLIM.lif') as lif:
...     for image in lif.images:
...         name = image.name
...     image = lif.images['Fast Flim']
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

__version__ = '2025.2.10'

__all__ = [
    '__version__',
    'imread',
    'logger',
    'xml2dict',
    'LifFile',
    'LifFileError',
    'LifFileFormat',
    'LifImage',
    'LifFlimImage',
    'LifImageABC',
    'LifImageSeries',
    'LifMemoryBlock',
    'FILE_EXTENSIONS',
]

import enum
import logging
import math
import os
import re
import struct
import sys
import warnings
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import cached_property
from typing import TYPE_CHECKING, final, overload
from urllib.parse import unquote
from xml.etree import ElementTree

if TYPE_CHECKING:
    from collections.abc import Container, Iterable, Iterator
    from typing import IO, Any, Literal

    from numpy.typing import DTypeLike, NDArray
    from xarray import DataArray

    OutputType = str | IO[bytes] | NDArray[Any] | None

import numpy

try:
    import imagecodecs
except ImportError:
    imagecodecs = None  # type: ignore[assignment]


@overload
def imread(
    file: str | os.PathLike[Any] | IO[bytes],
    /,
    image: int | str = 0,
    *,
    squeeze: bool = True,
    out: OutputType = None,
    asxarray: Literal[False] = ...,
    **kwargs: Any,
) -> NDArray[Any]: ...


@overload
def imread(
    file: str | os.PathLike[Any] | IO[bytes],
    /,
    image: int | str = 0,
    *,
    squeeze: bool = True,
    out: OutputType = None,
    asxarray: Literal[True] = ...,
    **kwargs: Any,
) -> DataArray: ...


def imread(
    file: str | os.PathLike[Any] | IO[bytes],
    /,
    image: int | str = 0,
    *,
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
        image:
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
        im = lif.images[image]
        if asxarray:
            data = im.asxarray(out=out, **kwargs)
        else:
            data = im.asarray(out=out, **kwargs)
    return data


class LifFileError(Exception):
    """Exception to indicate invalid Leica Image File structure."""


class LifFileFormat(enum.Enum):
    """Leica image file format."""

    LIF = 'LIF'
    """Leica image file."""

    LOF = 'LOF'
    """Leica object file containing single image."""

    XLIF = 'XLIF'
    """XML file containing image metadata."""

    XLEF = 'XLEF'
    """XML file containing experiment metadata."""

    XLLF = 'XLLF'
    """XML file containing folder-view metadata."""

    XLCF = 'XLCF'
    """XML file containing collection metadata."""

    LIFEXT = 'LIFEXT'
    """File containing optional image data for LIF."""


@final
class LifFile:
    """Leica image file (LIF, LOF, XLIF, XLEF, XLCF, or LIFEXT).

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
        _parent:
            Parent file, if any.

    Raises:
        LifFileError: File is not a Leica image file or is corrupted.

    """

    version: int
    """File version."""

    name: str
    """Name of file from XML header."""

    uuid: str | None
    """Unique identifier of file, if any."""

    format: LifFileFormat
    """Format of Leica image file."""

    xml_element: ElementTree.Element
    """XML header root element."""

    memory_blocks: dict[str, LifMemoryBlock]
    """Object memory blocks."""

    _fh: IO[bytes]
    _path: str  # absolute path of file
    _close: bool  # file needs to be closed
    _squeeze: bool  # remove dimensions of length one from images
    _xml_header: tuple[int, int]  # byte offset and size of XML header
    _parent: LifFile | None  # parent file, if any

    def __init__(
        self,
        file: str | os.PathLike[Any] | IO[bytes],
        /,
        *,
        squeeze: bool = True,
        mode: Literal['r', 'r+'] | None = None,
        _parent: LifFile | None = None,
    ) -> None:
        if isinstance(file, (str, os.PathLike)):
            if mode is None:
                mode = 'r'
            else:
                if mode[-1:] == 'b':
                    mode = mode[:-1]  # type: ignore[assignment]
                if mode not in {'r', 'r+'}:
                    raise ValueError(f'invalid mode {mode!r}')
            self._path = os.path.abspath(file)
            self._close = True
            self._fh = open(self._path, mode + 'b')
        elif hasattr(file, 'seek'):
            self._path = ''
            self._close = False
            self._fh = file
        else:
            raise ValueError(f'cannot open file of type {type(file)}')

        self._parent = _parent
        self._squeeze = bool(squeeze)
        self.format = LifFileFormat.LIF
        self.version = 0
        self.name = ''
        self.uuid = None
        self.memory_blocks = {}
        self._xml_header = (0, 0)
        self.xml_element = ElementTree.Element('')

        try:
            self._init()
        except Exception:
            self.close()
            raise

        if self._close and self.format in {
            LifFileFormat.XLIF,
            LifFileFormat.XLEF,
            LifFileFormat.XLCF,
        }:
            try:
                self._fh.close()
            except Exception:
                pass

    def _init(self) -> None:
        """Initialize from open file."""
        fh = self._fh
        # read binary header
        try:
            id0, size, id1, strlen = struct.unpack('<IIBI', fh.read(13))
        except Exception as exc:
            raise LifFileError('not a Leica image file') from exc

        if id0 in XML_CODEC:
            # XML: XLEF, XLCF, or XLIF
            self.format = LifFileFormat.XLIF
            self._xml_header = (0, -1)
            fh.seek(0)
            xml_header = fh.read().decode(XML_CODEC[id0])

        elif id0 == 0x70 and id1 == 0x2A:  # or size != 2 * strlen + 5
            self.format = LifFileFormat.LIF
            self._xml_header = (fh.tell(), strlen * 2)
            xml_header = fh.read(strlen * 2).decode('utf-16-le')

        else:
            raise LifFileError(
                'not a Leica image file '
                f'({id0=:02X} != 0x70 or {id1=:02X} != 0x2A)'
            )

        if xml_header == 'LMS_Object_File':
            self.format = LifFileFormat.LOF
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
            memblock = LifMemoryBlock(self)

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

        elif xml_header.startswith('<LMSDataContainerEnhancedHeader'):
            self.format = LifFileFormat.LIFEXT

        self.xml_element = ElementTree.fromstring(xml_header)
        del xml_header

        element = self.xml_element.find('./Element')
        if element is None:
            if self.format != LifFileFormat.LIFEXT:
                logger().warning(f'{self!r} Element element not found in XML')
        else:
            self.name = element.attrib.get('Name', self.name)
            self.uuid = element.attrib.get('UniqueID')

        # TODO: some XML found in (older?) LOF files do not contain a
        # versioned <LMSDataContainerHeader> element required by the
        # LOF specification, but instead start with <Data><Image> elements.
        # For now, let those files pass without exception, albeit with
        # an empty image series.

        try:
            self.version = int(self.xml_element.attrib['Version'])
        except KeyError:
            if not self.format == LifFileFormat.LOF:
                raise KeyError('Version attribute not found in XML')

        # add memory blocks
        if self.format == LifFileFormat.LOF:
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

        elif self.format in {LifFileFormat.LIF, LifFileFormat.LIFEXT}:
            while True:
                try:
                    memblock = LifMemoryBlock(self)
                except OSError:
                    break
                self.memory_blocks[memblock.id] = memblock

        elif self.format in {
            LifFileFormat.XLIF,
            LifFileFormat.XLEF,
            LifFileFormat.XLCF,
        }:
            assert element is not None
            if element.find('./Data/Collection') is not None:
                self.format = LifFileFormat.XLCF
            elif element.find('./Data/Experiment') is not None:
                self.format = LifFileFormat.XLEF
            memblock = LifMemoryBlock(self)
            self.memory_blocks[memblock.id] = memblock

        else:
            raise ValueError(f'unsupported format {self.format!r}')

    @property
    def filehandle(self) -> IO[bytes]:
        """File handle."""
        return self._fh

    @property
    def filename(self) -> str:
        """Name of file or empty if binary stream."""
        return os.path.basename(self._path)

    @property
    def dirname(self) -> str:
        """Directory containing file or empty if binary stream."""
        return os.path.dirname(self._path)

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
    def images(self) -> LifImageSeries:
        """Sequence of images in file."""
        return LifImageSeries(self)

    @property
    def series(self) -> LifImageSeries:
        # kept for backward compatibility with PhasorPy 0.4
        warnings.warn(
            'LifFile.series is deprecated. Use LifFile.images',
            DeprecationWarning,
            stacklevel=2,
        )
        return self.images

    @cached_property
    def children(self) -> tuple[LifFile, ...]:
        """Children references in XLEF and XLCF files."""
        dirname = self.dirname
        children: list[LifFile] = []
        for child in self.xml_element.findall('./Element/Children/Reference'):
            filename = child.attrib.get('File')
            if filename is None:
                continue
            filename = os.path.normpath(unquote(filename)).replace('\\', '/')
            filename = os.path.join(dirname, filename)
            filename = case_sensitive_path(filename)
            children.append(
                LifFile(filename, squeeze=self._squeeze, _parent=self)
            )
        return tuple(children)

    @property
    def parent(self) -> LifFile | None:
        """Parent file, if any."""
        return self._parent

    def xml_header(self) -> str:
        """Return XML object description from file."""
        xml: str | bytes

        if self._path and self._fh.closed:
            with open(self._path, 'rb') as fh:
                fh.seek(self._xml_header[0])
                xml = fh.read(self._xml_header[1])
        else:
            self._fh.seek(self._xml_header[0])
            xml = self._fh.read(self._xml_header[1])
        if self._xml_header[1] < 0:
            return xml.decode(XML_CODEC[xml[:4]])
        return xml.decode('utf-16-le')

    def close(self) -> None:
        """Close file handle and free resources."""
        if self._close:
            for child in self.children:
                child.close()
            try:
                self._fh.close()
            except Exception:
                pass

    def __enter__(self) -> LifFile:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        if self._path:
            name = self.filename
        elif hasattr(self._fh, 'name') and self._fh.name:
            name = os.path.basename(self._fh.name)
        else:
            name = self.name
        return (
            f'<{self.__class__.__name__} {name!r} images={len(self.images)}>'
        )

    def __str__(self) -> str:
        return indent(
            repr(self),
            f'path: {self._path}',
            f'format: {self.format}',
            f'uuid: {self.uuid}',
            f'datetime: {self.datetime}',
            indent(
                'images:',
                *(f'{i} {image!r}' for i, image in enumerate(self.images)),
            ),
            indent(
                'children:',
                *(f'{i} {child!r}' for i, child in enumerate(self.children)),
            ),
            indent(
                'memory_blocks:',
                *(
                    f'{i} {memblock}'
                    for i, memblock in enumerate(self.memory_blocks.values())
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

    def __init__(
        self,
        parent: LifFile,
        xml_element: ElementTree.Element,
        path: str,
        /,
    ) -> None:
        self.parent = parent
        self.xml_element = xml_element
        self.path = path

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
    def parent_image(self) -> LifImageABC | None:
        """Parent image, if any."""
        if '/' not in self.path:
            return None

        parent = self.parent
        while parent.parent is not None:
            parent = parent.parent

        dirname = self.path.rsplit('/', 1)[0]
        if self.parent.format != LifFileFormat.LIFEXT or '/' in dirname:
            return parent.images.find(f'^{dirname}$')

        # LIFEXT root image references image in parent LIF file
        # via MemoryBlockID
        if self.parent.parent is None:
            return None
        for image in self.parent.parent.images:
            if image.memory_block.id == dirname:
                return image
        return None

    @cached_property
    def child_images(self) -> tuple[LifImageABC, ...]:
        """Child images."""
        # return tuple(
        #     image
        #     for image in self.parent.images
        #     if image.parent_image is self
        # )
        return self.parent.images.findall(f'^{self.path}/[^/]*$')

    @cached_property
    def memory_block(self) -> LifMemoryBlock:
        """Memory block containing image data."""
        if self.parent.format in {LifFileFormat.LOF, LifFileFormat.XLIF}:
            # XLIF and LOF files contain one memory block
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
        path = self.path
        dtype = self.dtype
        prefix = ''
        sizes = ', '.join(f'{k}: {v}' for k, v in self.sizes.items())
        while True:
            r = f'<{name} {(prefix + path)!r} ({sizes}) {dtype}>'
            if len(r) < columns or '/' not in path:
                break
            path = path.split('/', 1)[-1]
            prefix += '…/'
        return r

    def __str__(self) -> str:
        return indent(
            repr(self),
            *(
                f'{name}: {getattr(self, name)!r}'[:160]
                for name in dir(self)
                if not (
                    name.startswith('_')
                    or name == 'xml_element_smd'
                    or callable(getattr(self, name))
                )
            ),
        )


@final
class LifImage(LifImageABC):
    """Regular image.

    Defined by XML Element with Data/Image child.

    """

    @property
    def xml_element_smd(self) -> ElementTree.Element | None:
        # for backward compatibility with PhasorPy 0.4
        warnings.warn(
            'LifImage.xml_element_smd is deprecated.',
            DeprecationWarning,
            stacklevel=2,
        )
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
        path = self.path
        if self.parent.format == LifFileFormat.LIF:
            path = self.parent.name + '/' + path
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
        mode: str = 'r',
        out: OutputType = None,
    ) -> NDArray[Any]:
        """Return image data as array.

        Dimensions are returned in order stored in file.

        Parameters:
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
                Image data as numpy array. RGB samples may not be contiguous.

        """
        data = self.memory_block.read_array(
            self.shape, self.dtype, mode=mode, out=out
        )
        if (
            len(self.memory_block.frames) == 0  # disable for frames
            and self.sizes.get('S', 0) == 3
            and self._channels[0].channel_tag == 3  # blue
            and self._channels[1].channel_tag == 2  # green
        ):
            # BGR to RGB
            data = data[..., ::-1]
        return data


@final
class LifFlimImage(LifImageABC):
    """FLIM/TCSPC histogram image.

    Defined by XML Element with Data/SingleMoleculeDetection child.

    """

    @property
    def xml_element_smd(self) -> ElementTree.Element | None:
        # for backward compatibility with PhasorPy 0.4
        warnings.warn(
            'LifImage.xml_element_smd is deprecated.',
            DeprecationWarning,
            stacklevel=2,
        )
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
    """Sequence of images in Leica image file."""

    __slots__ = ('_parent', '_images')

    _parent: LifFile
    _images: dict[str, LifImageABC]

    def __init__(self, parent: LifFile, /) -> None:
        self._parent = parent
        self._images = {}
        image: LifImageABC

        if parent.format not in {LifFileFormat.XLEF, LifFileFormat.XLCF}:
            keepbase = parent.format == LifFileFormat.LIFEXT
            for path, element in self._image_iter(parent.xml_element):
                if not keepbase:
                    path = path.split('/', 1)[-1]
                if element.find('./Data/SingleMoleculeDetection') is None:
                    image = LifImage(parent, element, path)
                else:
                    image = LifFlimImage(parent, element, path)
                self._images[path] = image

        for child in parent.children:
            for image in child.images:
                path = image.path
                if parent.format != LifFileFormat.XLEF:
                    path = f'{parent.name}/{path}'
                self._images[path] = image
                image.path = path
        return

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
        if len(elements) < 1:
            # LIFEXT root, use MemoryBlockID as base path
            childrenof = xml_element.find('./ChildrenOf')
            if childrenof is not None:
                base_path += childrenof.get('MemoryBlockID', '')
                elements = childrenof.findall('./Element')

        for element in elements:
            name = element.attrib['Name']
            if base_path == '':
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

    def find(
        self, key: str, /, *, flags: int = re.IGNORECASE, default: Any = None
    ) -> LifImageABC | None:
        """Return first image with matching path pattern, if any.

        Parameters:
            key:
                Regular expression pattern to match LifImage.path.
            flags:
                Regular expression flags.
            default:
                Value to return if no image with matching path found.

        """
        pattern = re.compile(key, flags=flags)
        for image in self._images.values():
            if pattern.search(image.path) is not None:
                return image
        return default  # type: ignore[no-any-return]

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
        for image in self._images.values():
            if pattern.search(image.path) is not None:
                images.append(image)
        return tuple(images)

    def __getitem__(  # type: ignore[override]
        self,
        key: int | str,
        /,
    ) -> LifImageABC:
        """Return image at index or first image with matching path.

        Raises:
            IndexError: if integer index out of range.
            KeyError: if no image with matching path found.

        """
        if isinstance(key, int):
            try:
                key = tuple(self._images.keys())[key]
            except IndexError:
                raise IndexError(f'image index={key} out of range')
            return self._images[key]
        if key in self._images:
            return self._images[key]
        pattern = re.compile(key, flags=re.IGNORECASE)
        for image in self._images.values():
            if pattern.search(image.path) is not None:
                return image
        raise KeyError(f'image {key!r} not found')

    def __len__(self) -> int:
        return len(self._images)

    def __iter__(self) -> Iterator[LifImageABC]:
        return iter(self._images.values())

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} len={len(self._images)}>'

    def __str__(self) -> str:
        return indent(
            repr(self),
            *(
                f'{i} {image!r}'
                for i, image in enumerate(self._images.values())
            ),
        )


@final
class LifMemoryBlock:
    """Object memory block.

    Parameters:
        parent: Underlying LIF file.

    """

    __slots__ = ('parent', 'id', 'offset', 'size', 'frames')

    parent: LifFile
    """Underlying LIF file."""

    id: str
    """Identity of memory block."""

    offset: int
    """Byte offset of memory block in file."""

    size: int
    """Size of memory block in bytes."""

    frames: tuple[LifMemoryFrame, ...]
    """Frames in memory block."""

    def __init__(self, parent: LifFile, /) -> None:
        self.parent = parent
        self.id = ''
        self.offset = -1
        self.size = 0
        self.frames = ()

        if parent.format in {LifFileFormat.XLEF, LifFileFormat.XLCF}:
            return

        if parent.format == LifFileFormat.XLIF:
            memory = parent.xml_element.find('./Element/Memory')
            if memory is None:
                raise ValueError('Memory element not found in XML')
            self.offset = -1
            self.size = int(memory.attrib['Size'])
            self.id = memory.get('MemoryBlockID', '')
            frames = []
            for block in memory:
                # Frame, Block, OMETiffBlock, AiviaTiffBlock, ...
                if 'File' not in block.attrib:
                    continue
                file = block.attrib['File']
                offset = int(block.attrib['Offset'])
                size = int(block.attrib['Size'])
                uuid = block.get('UUID', '')
                frames.append(LifMemoryFrame(file, offset, size, uuid))
            self.frames = tuple(frames)
            return

        if parent.format == LifFileFormat.LOF:
            fmtstr = '<BQ'
        elif parent.version == 2 or parent.format == LifFileFormat.LIFEXT:
            fmtstr = '<IIBQBI'
        elif parent.version == 1:
            fmtstr = '<IIBIBI'
        else:
            raise ValueError(f'invalid memory block {parent.version=}')

        fh = parent.filehandle
        size = struct.calcsize(fmtstr)
        buffer = fh.read(size)
        if len(buffer) != size:
            raise OSError

        if parent.format == LifFileFormat.LOF:
            self.id = 'MemBlock_0'  # updated in LifFile._init
            id0, size = struct.unpack(fmtstr, buffer)
            if id0 != 0x2A:
                raise LifFileError(
                    f'corrupted LOF memory block ({id0=:02X} != 0x2A)'
                )
        else:
            # parent.format == LifFileFormat.LIF:
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
            size = size1

        offset = fh.tell()
        fh.seek(size, 1)
        if fh.tell() - offset != size:
            raise OSError
        self.offset = offset
        self.size = size

    def read(self, /) -> bytes:
        """Return memory block from file."""
        buffer: bytes | bytearray

        if len(self.frames) == 1 and self.frames[0].file.endswith('.lof'):
            # allow reading FLIM data from LOF file
            path = case_sensitive_path(
                os.path.join(self.parent.dirname, self.frames[0].file)
            )
            with LifFile(path) as lof:
                data = lof.images[0].memory_block.read()
            return data
        if len(self.frames) > 0:
            dirname = self.parent.dirname
            buffer = bytearray(self.size)
            for frame in self.frames:
                im = frame.imread(dirname)
                buffer[frame.offset : frame.offset + frame.size] = im.tobytes()
            return bytes(buffer)

        self.parent.filehandle.seek(self.offset)
        buffer = self.parent.filehandle.read(self.size)
        if len(buffer) != self.size:
            raise OSError(f'read {len(buffer)} bytes, expected {self.size}')
        return buffer

    def readinto(self, buffer: NDArray[Any], /) -> None:
        """Read memory block from file into contiguous ndarray."""
        if not buffer.flags.c_contiguous:
            raise ValueError('buffer must be contiguous')
        if buffer.nbytes != self.size:
            raise ValueError(f'{buffer.nbytes} != {self.size=}')
        buffer = buffer.reshape(-1).view(numpy.uint8)

        if self.parent.format == LifFileFormat.XLIF:
            for frame in self.frames:
                im = frame.imread(self.parent.dirname)
                im = im.reshape(-1).view(numpy.uint8)
                buffer[frame.offset : frame.offset + frame.size] = im
            return

        fh = self.parent.filehandle
        fh.seek(self.offset)
        try:
            nbytes = fh.readinto(buffer)  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            data = fh.read(self.size)
            nbytes = len(data)
            buffer[:] = numpy.frombuffer(data, numpy.uint8)

        if nbytes != self.size:
            raise OSError(f'read {nbytes} bytes, expected {self.size}')

    def read_array(
        self,
        shape: tuple[int, ...],
        dtype: DTypeLike,
        *,
        mode: str = 'r',
        out: OutputType = None,
    ) -> NDArray[Any]:
        """Return NumPy array from file.

        Parameters:
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

        fh = self.parent.filehandle

        if isinstance(out, str) and out == 'memmap' and self.offset > 0:
            return numpy.memmap(  # type: ignore[no-any-return]
                fh,  # type: ignore[call-overload]
                dtype=dtype,
                mode=mode,
                offset=self.offset,
                shape=shape,
                order='C',
            )

        if (
            out is None
            and self.parent.format == LifFileFormat.XLIF
            and len(self.frames) == 1
        ):
            # avoid copy single frame to output array
            data = self.frames[0].imread(self.parent.dirname)
            # create view in case float16 are stored as uint16 in TIFF
            return data.view(dtype).reshape(shape)

        data = create_output(out, shape, dtype)
        if data.nbytes != nbytes:
            raise ValueError('size mismatch')

        self.readinto(data)

        if out is not None:
            if hasattr(out, 'flush'):
                out.flush()

        return data

    def __repr__(self) -> str:
        frames = f' frames={len(self.frames)}' if len(self.frames) > 0 else ''
        return (
            f'<{self.__class__.__name__} {self.id!r} '
            f'offset={self.offset} size={self.size}{frames}>'
        )


@final
class LifMemoryFrame:
    """Frame in object memory block."""

    __slots__ = ('file', 'offset', 'size', 'uuid')

    file: str
    """File name."""

    offset: int
    """Byte offset of frame in memory block."""

    size: int
    """Size of frame in bytes."""

    uuid: str
    """Unique identifier of frame."""

    def __init__(
        self,
        file: str,
        offset: int,
        size: int,
        uuid: str,
        /,
    ) -> None:
        self.file = os.path.normpath(unquote(file)).replace('\\', '/')
        self.offset = int(offset)
        self.size = int(size)
        self.uuid = uuid

    def imread(
        self,
        dirname: str,
        /,
        **kwargs: Any,
    ) -> NDArray[Any]:
        """Return image frame from file.

        Parameters:
            dirname: Directory name of parent file.
            **kwargs: Optional arguments to image reader function.

        """
        ext = os.path.splitext(self.file)[1].lower()
        if ext not in IMREAD:
            raise ValueError(f'unsupported file extension {ext!r}')
        path = case_sensitive_path(os.path.join(dirname, self.file))
        im = IMREAD[ext](path, **kwargs)
        if im.nbytes != self.size:
            if (
                im.ndim == 3
                and im.shape[2] == 3
                and im.nbytes // 3 == self.size
            ):
                # RGB -> grayscale
                im = im[:, :, 0]
            else:
                raise ValueError(f'{self.size!r} != array size={im.nbytes}')
        return im

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} {self.file!r} '
            f'offset={self.offset} size={self.size} uiud={self.uuid!r}>'
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
    """Raw data format."""
    voxel_size_x: float
    """Spatial dimension size in m."""
    voxel_size_y: float
    """Spatial dimension size in m."""
    voxel_size_z: float
    """Spatial dimension size in m."""
    clock_period: float
    """Base clock in s."""
    synchronization_marker_period: float
    """Clock period of the FCS counter in s."""
    frame_repetitions_marked: bool
    """Frames completed when number photons detected."""
    pixel_time: str
    """Pixel dwell time in s."""
    bi_directional: bool
    """Bi-directional scan."""
    sequential_mode: bool
    """Look Up Table is inverted."""


if imagecodecs is not None:

    def imread_tif(filename: str, /, **kwargs: Any) -> NDArray[Any]:
        with open(filename, 'rb') as fh:
            data = fh.read()
        return imagecodecs.tiff_decode(data, index=None, **kwargs)

    def imread_jpg(filename: str, /, **kwargs: Any) -> NDArray[Any]:
        with open(filename, 'rb') as fh:
            data = fh.read()
        return imagecodecs.jpeg8_decode(data, **kwargs)

    def imread_png(filename: str, /, **kwargs: Any) -> NDArray[Any]:
        with open(filename, 'rb') as fh:
            data = fh.read()
        return imagecodecs.png_decode(data, **kwargs)

    def imread_bmp(filename: str, /, **kwargs: Any) -> NDArray[Any]:
        with open(filename, 'rb') as fh:
            data = fh.read()
        return imagecodecs.bmp_decode(data, **kwargs)

else:

    def imread_fail(  # type: ignore[unreachable]
        filename: str, /, **kwargs: Any
    ) -> NDArray[Any]:
        raise ImportError(
            f'reading {os.path.splitext(filename)!r} '
            "files requires the 'imagecodecs' package"
        )

    imread_tif = imread_jpg = imread_png = imread_bmp = imread_fail


IMREAD: dict[str, Callable[..., NDArray[Any]]] = {
    '.lof': imread,
    '.tif': imread_tif,
    '.jpg': imread_jpg,
    '.png': imread_png,
    '.bmp': imread_bmp,
}
"""Leica image file reader functions."""

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


XML_CODEC = {
    # struct.unpack('<I', '<?xml'.encode(codec)[:4])[0]
    b'<?xm': 'utf-8',
    b'\xef\xbb\xbf<': 'utf-8-sig',
    b'<\x00?\x00': 'utf-16-le',
    b'\x00<\x00?': 'utf-16-be',
    b'\xff\xfe<\x00': 'utf-16',
    1836597052: 'utf-8',
    1019198447: 'utf-8-sig',
    4128828: 'utf-16-le',
    1056979968: 'utf-16-be',
    3997439: 'utf-16',
}
"""Map XML first four bytes to codec."""


FILE_EXTENSIONS = {
    '.lif': LifFile,
    '.lof': LifFile,
    '.xlif': LifFile,
    '.xlef': LifFile,
    '.xlcf': LifFile,
    # '.xllf': LifFile,
    # '.lifext': LifFileExt,
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


def case_sensitive_path(path: str | os.PathLike[str], /) -> str:
    """Return actual case of path."""
    if os.path.exists(path):
        return str(path)
    path = os.path.abspath(path)
    dirname, basename = os.path.split(path)
    if dirname == path:
        return dirname
    dirname = case_sensitive_path(dirname)
    basename = basename.lower()
    for child in os.listdir(dirname):
        if child.lower() == basename:
            return os.path.join(dirname, child)
    raise FileNotFoundError(f'{str(path)!r} not found')


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
        files = glob(f'{argv[1]}/*.*l?f')
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
                for i, image in enumerate(lif.images):
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
                            show=i == len(lif.images) - 1,
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
