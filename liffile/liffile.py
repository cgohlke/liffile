# liffile.py

# Copyright (c) 2023-2026, Christoph Gohlke
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

"""Read Leica image files (LIF, LOF, XLIF, XLEF, XLCF, XLLF, and LIFEXT).

Liffile is a Python library to read image and metadata from Leica image files:
LIF (Leica Image File), LOF (Leica Object File), XLIF (XML Image File),
XLCF (XML Collection File), XLEF (XML Experiment File), XLLF (XML Folder
View File), and LIFEXT (Leica Image File Extension). These files are written
by LAS X software to store collections of images and metadata from microscopy
experiments.

:Author: `Christoph Gohlke <https://www.cgohlke.com>`_
:License: BSD-3-Clause
:Version: 2026.10.8
:DOI: `10.5281/zenodo.14740657 <https://doi.org/10.5281/zenodo.14740657>`_

Quickstart
----------

Install the liffile package and all dependencies from the
`Python Package Index <https://pypi.org/project/liffile/>`_::

    python -m pip install -U liffile[all]

See `Examples`_ and `Documentation <https://www.cgohlke.com/docs/liffile/>`_
for using the programming interface.

Source code and support are available on
`GitHub <https://github.com/cgohlke/liffile>`_.

Requirements
------------

This revision was tested with the following requirements and dependencies
(other versions may work):

- `CPython <https://www.python.org>`_ 3.12.10, 3.13.16, 3.14.8, 3.15.0rc 64-bit
- `Numpy <https://pypi.org/project/numpy>`_ 2.5.3
- `Imagecodecs <https://pypi.org/project/imagecodecs>`_ 2026.8.16
  (required for decoding TIFF, JPEG, PNG, and BMP)
- `Tifffile <https://pypi.org/project/tifffile/>`_ 2026.9.20
  (required for reading multi-page TIFF)
- `Xarray <https://pypi.org/project/xarray>`_ 2026.9.0 (recommended)
- `Matplotlib <https://pypi.org/project/matplotlib/>`_ 3.11.2 (optional)

Revisions
---------

2026.10.8

- Support XLLF (folder view) files.

2026.10.3

- Do not remove images with duplicate paths (bioio-lif issue 55).

2026.7.14

- Add option to memory-map LIF files.
- Drop support for numpy 2.0 (SPEC0).
- Support Python 3.15.

2026.4.11

- Add channel name resolution to LifImage via coords['C'] and coords['S'].
- Drop support for Python 3.11.

2026.2.16

- Change timestamps to None if not present (breaking).
- Fix inefficient timestamp parsing.
- Fix inefficient LifFile.close().
- Add tilescan property to LifImage.

2026.2.15

- Add experimental frame-based interface to LifImage.
- Fix code review issues.

2026.1.22

- Fix reading sequence of LifMemoryBlocks.
- Change unknown axis code to '?'.

2026.1.14

- …

Refer to the CHANGES file for older revisions.

Notes
-----

The API is not stable yet and might change between revisions.

`Leica Microsystems GmbH <https://www.leica.com/>`_ is a manufacturer of
microscopes and scientific instruments.
Leica image files are proprietary formats written by Leica acquisition
software such as LAS X and LAS AF to store microscopy images and metadata.

The Leica Image File (LIF) begins with a magic number followed by a UTF-16
XML header that describes images and metadata, then stores the raw pixel data
for each image in contiguous data blocks.
Images may be multi-dimensional (X, Y, Z, T, C, ...) with multiple channels,
and a single file can contain many independent image series.
Related formats include LOF (single-object variant), XLIF, XLEF, and XLCF
(XML-based containers), XLLF (folder-view), and LIFEXT (optional image data
extensions).

This library is not feature-complete. Unsupported features currently include
image mosaics and pyramids, bit increments, and non-image data such as
raw FLIM/TCSPC histogram data.

The library has been tested with only a limited number of version 2 files.

The Leica image file formats are documented in:

- Leica Image File Formats - LIF, XLEF, XLLF, LOF. Version 3.2.
  Leica Microsystems GmbH. 21 September 2016.
- Annotations to Leica Image File Formats for LAS X Version 3.x. Version 1.4.
  Leica Microsystems GmbH. 24 August 2016.
- TSC SP8 FALCON File Format Description. LAS X Version 3.5.0.

Other implementations for reading Leica image files are
`readlif <https://github.com/Arcadia-Science/readlif>`_ and
`Bio-Formats <https://github.com/ome/bioformats>`_.

Examples
--------

Import functions and classes used in these examples:

>>> from liffile import LifFile

Read a FLIM lifetime image and metadata from a LIF file:

>>> with LifFile('tests/data/FLIM.lif') as lif:
...     for image in lif.images:
...         _ = image.name
...     image = lif.images['Fast Flim']  # by name
...     assert image.dtype == 'float16'
...     assert image.sizes == {'Y': 1024, 'X': 1024}
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
    UniqueID:       694efd02-95a9-436e-0fa6-f146120b1e15
    F16:            {'Name': 'F16',...
    TileScanInfo:   {'Tile': {'FieldX': 0,...
    ViewerScaling:  {'ChannelScalingInfo': {...

Iterate over selected XLEF image frames in ZTM dimension order:

>>> with LifFile('tests/data/XYZCST/XYZCST.xlef') as lif:
...     image = lif.images[0]  # by index
...     image.sizes
...     frames = image.frames(C=1, Z=slice(1, 3), T=[1, 0], M=None)
...     frames.sizes
...     for index, frame in frames.items():
...         index, frame.shape
...
{'T': 2, 'M': 4, 'C': 3, 'Z': 5, 'Y': 1200, 'X': 1600}
{'Z': 2, 'T': 2, 'M': 4, 'Y': 1200, 'X': 1600}
((0, 0, 0), (1200, 1600))
((0, 0, 1), (1200, 1600))
...
((1, 1, 2), (1200, 1600))
((1, 1, 3), (1200, 1600))

View image and metadata in a LIF file from the console::

    $ python -m liffile tests/data/FLIM.lif

"""

from __future__ import annotations

__version__ = '2026.10.8'

__all__ = [
    'FILE_EXTENSIONS',
    'LifFile',
    'LifFileError',
    'LifFileType',
    'LifFlimImage',
    'LifImage',
    'LifImageABC',
    'LifImageFrames',
    'LifImageSeries',
    'LifMemoryBlock',
    'LifMemoryBlockType',
    'LifTileScanInfo',
    '__version__',
    'imread',
    'xml2dict',
]

import contextlib
import enum
import io
import itertools
import logging
import math
import mmap
import os
import re
import struct
import sys
import threading
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import cached_property, lru_cache
from typing import TYPE_CHECKING, final, overload, override
from urllib.parse import unquote
from xml.etree import ElementTree

if TYPE_CHECKING:
    from collections.abc import Container, Iterable, Iterator
    from types import TracebackType
    from typing import IO, Any, ClassVar, Literal, Self

    from numpy.typing import DTypeLike, NDArray
    from tifffile import TiffFile
    from xarray import DataArray

    OutputType = str | IO[bytes] | NDArray[Any] | None
    SelectionValue = int | slice | Sequence[int] | None
    SelectionType = dict[str, SelectionValue]

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
    selection: SelectionType | None = None,
    memmap: bool = False,
    squeeze: bool = True,
    asxarray: Literal[False] = ...,
    out: OutputType = None,
    **kwargs: Any,
) -> NDArray[Any]: ...


@overload
def imread(
    file: str | os.PathLike[Any] | IO[bytes],
    /,
    image: int | str = 0,
    *,
    selection: SelectionType | None = None,
    memmap: bool = False,
    squeeze: bool = True,
    asxarray: Literal[True] = ...,
    out: OutputType = None,
    **kwargs: Any,
) -> DataArray: ...


def imread(
    file: str | os.PathLike[Any] | IO[bytes],
    /,
    image: int | str = 0,
    *,
    selection: SelectionType | None = None,
    memmap: bool = False,
    squeeze: bool = True,
    asxarray: bool = False,
    out: OutputType = None,
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
        selection:
            Per-dimension selection using case-sensitive dimension codes.
            If ``None``, return entire image.
            Otherwise, a dict mapping dimension names to selection values:

            - ``int``: Fixed index.
            - ``slice``: Range of indices.
            - ``Sequence[int]``: Specific indices.
            - ``None``: All indices.

            Not supported with RAW FLIM images.
        memmap:
            Map file into memory.
            Ignored if memory mapping is not available or if the stream does
            not support it.
        squeeze:
            Remove dimensions of length one from images.
        asxarray:
            Return image data as xarray.DataArray instead of numpy.ndarray.
        out:
            Specifies where to copy image data.
            If ``None``, create a new NumPy array in main memory.
            If ``'memmap'``, directly memory-map the image data in the file.
            If a ``numpy.ndarray``, a writable, initialized array
            of compatible shape and dtype.
            If a ``file name`` or ``open file``, create a memory-mapped
            array in the specified file.
        **kwargs:
            Optional arguments to :py:meth:`LifImageABC.asarray`,
            :py:meth:`LifImageABC.asxarray`, or :py:meth:`LifImage.frames`.

    Returns:
        :
            Image data as numpy array or xarray DataArray.

    """
    with LifFile(file, memmap=memmap, squeeze=squeeze) as lif:
        im = lif.images[image]

        if selection is None:
            if asxarray:
                return im.asxarray(out=out, **kwargs)
            return im.asarray(out=out, **kwargs)

        if isinstance(im, LifFlimImage):
            msg = 'selection not supported with LifFlimImage'
            raise NotImplementedError(msg)

        frames = im.frames(**selection)
        if asxarray:
            return frames.asxarray(out=out, **kwargs)
        return frames.asarray(out=out, **kwargs)


class LifFileError(ValueError):
    """Exception to indicate invalid Leica Image File structure."""


class LifFileType(enum.Enum):
    """Leica image file type."""

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


class BinaryFile:
    """Binary file.

    Parameters:
        file:
            File name or seekable binary stream.
        mode:
            File open mode if ``file`` is a file name.
            If not specified, defaults to ``'r'``. Files are always opened
            in binary mode.
        memmap:
            Map file into memory.
            Ignored if memory mapping is not available or if the stream does
            not support it.

    Notes:
        Memory mapping can improve random-access read performance on large
        files or repeated reads of the same file regions by reducing syscall
        overhead and data copying.
        For sequential one-pass reads, regular buffered I/O may be faster.

    Raises:
        TypeError:
            File is a text stream, or an unsupported type.
        ValueError:
            Invalid file name, extension, or stream.
            File stream is not seekable.

    """

    _fh: IO[bytes]
    _mm: mmap.mmap | None
    _mv: memoryview | None  # view of _mm
    _path: str  # absolute path of file
    _name: str  # name of file or handle
    _close: bool  # file needs to be closed
    _closed: bool  # file is closed
    _memmap: bool  # open companion files using memmap
    _lock: contextlib.AbstractContextManager[Any]
    _ext: ClassVar[set[str]] = set()  # valid extensions, empty for any

    def __init__(
        self,
        file: str | os.PathLike[str] | IO[bytes],
        /,
        *,
        mode: Literal['r', 'r+'] | None = None,
        memmap: bool = False,
    ) -> None:

        self._mm = None
        self._mv = None
        self._path = ''
        self._name = 'Unnamed'
        self._close = False
        self._closed = False
        self._memmap = bool(memmap)
        self._lock = contextlib.nullcontext()

        if isinstance(file, (str, os.PathLike)):
            ext = os.path.splitext(file)[-1].lower()
            if self._ext and ext not in self._ext:
                msg = f'invalid file extension: {ext!r} not in {self._ext!r}'
                raise ValueError(msg)
            if mode is None:
                mode = 'r'
            else:
                if mode[-1:] == 'b':
                    # accept 'rb'/'r+b'
                    mode = mode[:-1]  # type: ignore[assignment]
                if mode not in {'r', 'r+'}:
                    msg = f'invalid {mode=!r}'
                    raise ValueError(msg)
            self._path = os.path.abspath(file)
            self._close = True
            self._fh = open(self._path, mode + 'b')  # noqa: SIM115

        elif hasattr(file, 'seek'):
            # binary stream: open file, BytesIO, fsspec LocalFileOpener
            if isinstance(file, io.TextIOBase):  # type: ignore[unreachable]
                msg = (  # type: ignore[unreachable]
                    f'{file=!r} is not open in binary mode'
                )
                raise TypeError(msg)

            self._fh = file
            try:
                self._fh.tell()
            except Exception as exc:
                msg = f'{file=!r} is not seekable'
                raise ValueError(msg) from exc
            if hasattr(file, 'path'):
                self._path = os.path.abspath(file.path)
            elif hasattr(file, 'name'):
                self._path = os.path.abspath(file.name)

        elif hasattr(file, 'open'):
            # fsspec OpenFile
            self._fh = file.open()
            self._close = True
            try:
                self._fh.tell()
            except Exception as exc:
                with contextlib.suppress(Exception):
                    self._fh.close()
                msg = f'{file=!r} is not seekable'
                raise ValueError(msg) from exc
            if hasattr(file, 'path'):
                self._path = os.path.abspath(file.path)

        else:
            msg = f'cannot handle {type(file)=}'
            raise TypeError(msg)

        if hasattr(file, 'name') and file.name:
            self._name = os.path.basename(file.name)
        elif self._path:
            self._name = os.path.basename(self._path)
        else:
            self._name = type(file).__name__

        if memmap:
            _fh: Any = self._fh
            if isinstance(_fh, mmap.mmap):
                self._mm = _fh
                self._mv = memoryview(self._mm)
            else:
                try:
                    access = (
                        mmap.ACCESS_WRITE
                        if self._fh.writable()
                        else mmap.ACCESS_READ
                    )
                    self._mm = mmap.mmap(self._fh.fileno(), 0, access=access)
                    self._mv = memoryview(self._mm)
                except OSError:
                    pass

    @property
    def filehandle(self) -> IO[bytes]:
        """File handle."""
        return self._fh

    @property
    def filepath(self) -> str:
        """Absolute path to file, or empty string if no path is available."""
        return self._path

    @property
    def filename(self) -> str:
        """Basename of file path, or empty string if no path is available."""
        return os.path.basename(self._path)

    @property
    def dirname(self) -> str:
        """Directory containing file, or empty string if no path available."""
        return os.path.dirname(self._path)

    @property
    def name(self) -> str:
        """Display name of file."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def attrs(self) -> dict[str, Any]:
        """Selected metadata as dict."""
        return {'name': self.name, 'filepath': self.filepath}

    @property
    def lock(self) -> contextlib.AbstractContextManager[Any]:
        """Lock for thread-safe file access."""
        return self._lock

    def set_lock(self, enabled: bool, /) -> None:  # noqa: FBT001
        """Enable or disable thread-safe file access.

        Parameters:
            enabled:
                If true, use a threading.RLock, else a no-op lock.
                Has no effect when memory-mapped I/O is active.

        """
        if self._mm is not None:
            return
        self._lock = threading.RLock() if enabled else contextlib.nullcontext()

    def _write_at(
        self, offset: int, data: bytes | bytearray | memoryview, /
    ) -> None:
        """Write bytes to file at given offset.

        Parameters:
            offset: Byte offset from start of file.
            data: Data to write.

        """
        if self._mm is not None and self.writable:
            # writable mmap: direct slice write, no cursor movement
            self._mm[offset : offset + len(data)] = data
        else:
            with self._lock:
                self._fh.seek(offset)
                self._fh.write(data)

    def _read_at(self, offset: int, size: int, /) -> bytes | memoryview:
        """Read bytes from file at given offset.

        For memory-mapped files, returned bytes are exposed as a
        ``memoryview`` of the mapping. Keeping that view alive may keep
        the memory map (and associated file resources/lock) alive.

        Parameters:
            offset: Byte offset from start of file.
            size: Number of bytes to read.

        """
        mv = self._mv
        if mv is not None:
            return mv[offset : offset + size]
        fh = self._fh
        with self._lock:
            fh.seek(offset)
            return fh.read(size)

    def _read_into(self, offset: int, buffer: NDArray[numpy.uint8], /) -> int:
        """Read bytes from file at given offset into existing buffer.

        Parameters:
            offset: Byte offset from start of file.
            buffer: Flat, writable uint8 numpy array to read into.

        Returns:
            Number of bytes read.

        """
        nbytes = len(buffer)
        mv = self._mv
        if mv is not None:
            n = min(nbytes, max(0, len(mv) - offset))
            buffer[:n] = numpy.frombuffer(mv[offset : offset + n], numpy.uint8)
            return n

        fh = self._fh
        with self._lock:
            fh.seek(offset)
            try:
                return fh.readinto(buffer)  # type: ignore[attr-defined, no-any-return]
            except (AttributeError, OSError):
                data = fh.read(nbytes)
                buffer[:] = numpy.frombuffer(data, numpy.uint8)
                return len(data)

    def _read_array(
        self,
        offset: int,
        count: int,
        dtype: DTypeLike,
        *,
        copy: bool = False,
        writable: bool = False,
        truncate: bool | None = False,
    ) -> NDArray[Any]:
        """Read numpy array from file at given offset.

        For memory-mapped files, returned data are exposed directly as a
        NumPy array view of the mapping (zero copy). Keeping that array alive
        may keep the memory map (and associated file resources/lock) alive.

        Parameters:
            offset:
                Byte offset from start of file.
            count:
                Number of elements to read. If ``-1``, read to end of file.
            dtype:
                Array element type.
            copy:
                If true, always return a detached copy in main memory.
                For memory-mapped files, bypass the direct-view fast path.
            writable:
                By default, return read-only array from memory-mapped file.
                Prevents accidental modification of underlying writable file.
                Has no effect for non-memory-mapped files (always writable).
            truncate:
                Allow partial reads of array.
                If None, log error on partial read.

        """
        dtype = numpy.dtype(dtype)
        itemsize = dtype.itemsize
        if offset < 0:
            msg = f'{offset=} < 0'
            raise ValueError(msg)
        if count < -1:
            msg = f'{count=} < -1'
            raise ValueError(msg)

        mv = self._mv
        if mv is not None:
            if count == -1:
                count = max(0, (len(mv) - offset) // itemsize)
            nbytes = count * itemsize
            size = min(nbytes, max(0, len(mv) - offset))
            n = size - size % itemsize
            array = numpy.frombuffer(
                mv[offset : offset + n],
                dtype,
            )
            if copy:
                array = array.copy()
            elif not writable and array.flags.writeable:
                array.flags.writeable = False
        elif count > -1:
            fh = self._fh
            nbytes = count * itemsize
            array = numpy.empty(count, dtype)
            with self._lock:
                fh.seek(offset)
                n = fh.readinto(array.data)  # type: ignore[attr-defined]
        else:
            fh = self._fh
            with self._lock:
                fh.seek(0, os.SEEK_END)
                size = fh.tell()
                count = max(0, (size - offset) // itemsize)
                nbytes = count * itemsize
                array = numpy.empty(count, dtype)
                fh.seek(offset)
                n = fh.readinto(array.data)  # type: ignore[attr-defined]

        if n != nbytes:
            array = array[: n // itemsize]
            msg = f'expected {count} items, got {n // itemsize}'
            if truncate is None:
                logging.getLogger(__name__.split('.', 1)[0]).error(msg)
            elif not truncate:
                raise ValueError(msg)

        return array

    @cached_property
    def filesize(self) -> int:
        """Size of file in bytes."""
        if self._mm is not None:
            return len(self._mm)
        fh = self._fh
        try:
            return os.fstat(fh.fileno()).st_size
        except (AttributeError, io.UnsupportedOperation, OSError):
            pass
        with self._lock:
            pos = fh.tell()
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            fh.seek(pos)
        return size

    @property
    def writable(self) -> bool:
        """File is open for writing."""
        return self._fh.writable()

    @property
    def memmapped(self) -> bool:
        """File is memory-mapped."""
        return self._mm is not None

    @property
    def closed(self) -> bool:
        """File is closed."""
        return self._closed

    def close(self) -> None:
        """Close file."""
        self._closed = True  # always report file as closed
        self._mv = None  # do not release(), threads may hold local refs
        if self._mm is not None and self._mm is not self._fh:  # type: ignore[comparison-overlap]
            with contextlib.suppress(Exception):
                self._mm.close()
        if self._close:
            with contextlib.suppress(Exception):
                self._fh.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} {self._name!r}>'


@final
class LifFile(BinaryFile):
    """Leica image file (LIF, LOF, XLIF, XLEF, XLCF, XLLF, and LIFEXT).

    ``LifFile`` instances are not thread-safe. All attributes are read-only.

    ``LifFile`` instances must be closed with :py:meth:`LifFile.close`,
    which is automatically called when using the 'with' context manager.

    Parameters:
        file:
            Name of Leica image file or seekable binary stream.
        mode:
            File open mode if ``file`` is a file name.
            If not specified, defaults to ``'r'``. Files are always opened
            in binary mode.
        memmap:
            Map file into memory.
            Ignored if memory mapping is not available or if the stream does
            not support it.
        squeeze:
            Remove dimensions of length one from images.
        _parent:
            Parent file, if any.

    Raises:
        LifFileError: File is not a Leica image file or is corrupted.

    """

    type: LifFileType
    """Type of Leica image file."""

    version: int
    """File version."""

    uuid: str | None
    """Unique identifier of file, if any."""

    xml_element: ElementTree.Element
    """XML header root element."""

    memory_blocks: dict[str, LifMemoryBlock]
    """Object memory blocks."""

    _squeeze: bool  # remove dimensions of length one from images
    _xml_header: tuple[int, int]  # byte offset and size of XML header
    _parent: LifFile | None  # parent file, if any
    _open_files: list[LifFile | TiffFile]  # files to close

    def __init__(
        self,
        file: str | os.PathLike[Any] | IO[bytes],
        /,
        *,
        mode: Literal['r', 'r+'] | None = None,
        memmap: bool = False,
        squeeze: bool = True,
        _parent: LifFile | None = None,
    ) -> None:
        super().__init__(file, mode=mode, memmap=memmap)

        self._parent = _parent
        self._squeeze = bool(squeeze)
        self._open_files = []
        self.type = LifFileType.LIF
        self.version = 0
        self.uuid = None
        self.memory_blocks = {}
        self._xml_header = (0, 0)
        self.xml_element = ElementTree.Element('')

        try:
            self._init()
        except BaseException:
            self.close()
            raise

        if self._close and self.type in {
            LifFileType.XLIF,
            LifFileType.XLEF,
            LifFileType.XLCF,
            LifFileType.XLLF,
        }:
            with contextlib.suppress(Exception):
                self._fh.close()

    def _init(self) -> None:
        """Initialize from open file."""
        fh = self._fh
        # read binary header
        try:
            id0, size, id1, strlen = struct.unpack('<IIBI', fh.read(13))
        except Exception as exc:
            msg = 'not a Leica image file'
            raise LifFileError(msg) from exc

        if id0 in XML_CODEC:
            # XML: XLEF, XLCF, or XLIF
            self.type = LifFileType.XLIF
            self._xml_header = (0, -1)
            fh.seek(0)
            xml_header = fh.read().decode(XML_CODEC[id0])

        elif id0 == 0x70 and id1 == 0x2A:  # or size != 2 * strlen + 5
            self.type = LifFileType.LIF
            self._xml_header = (fh.tell(), strlen * 2)
            xml_header = fh.read(strlen * 2).decode('utf-16-le')

        else:
            msg = (
                'not a Leica image file '
                f'({id0=:02X} != 0x70 or {id1=:02X} != 0x2A)'
            )
            raise LifFileError(msg)

        if xml_header == 'LMS_Object_File':
            self.type = LifFileType.LOF
            # read memory block
            try:
                id0, _ver0, id1, _ver1 = struct.unpack('<BIBI', fh.read(10))
            except Exception as exc:
                msg = 'corrupted Leica object file'
                raise LifFileError(msg) from exc
            if id0 != 0x2A or id1 != 0x2A:
                msg = (
                    'corrupted Leica object file '
                    f'({id0=:02X} != 0x2A or {id1=:02X} != 0x2A)'
                )
                raise LifFileError(msg)
            memblock = LifMemoryBlock(self)

            # read XML header
            try:
                id0, size, id1, xmlsize = struct.unpack('<IIBI', fh.read(13))
            except Exception as exc:
                msg = 'corrupted Leica object file'
                raise LifFileError(msg) from exc
            if id0 != 0x70 or id1 != 0x2A or size != 2 * xmlsize + 5:
                msg = (
                    'corrupted Leica object file '
                    f'({id0=:02X} != 0x70, {id1=:02X} != 0x2A, or '
                    f'{size=} != {2 * xmlsize + 5})'
                )
                raise LifFileError(msg)
            self._xml_header = (fh.tell(), xmlsize * 2)
            xml_header = fh.read(xmlsize * 2).decode('utf-16-le')

            if xml_header.startswith('<Data>'):
                # Some XML found in (older?) LOF files do not contain a
                # versioned <LMSDataContainerHeader> element required by
                # the LOF specification, but instead start with <Data><Image>
                # elements.
                if self._path:
                    name = os.path.splitext(os.path.basename(self._path))[0]
                elif hasattr(self._fh, 'name') and self._fh.name:
                    name = os.path.splitext(os.path.basename(self._fh.name))[0]
                else:
                    name = 'Unnamed'
                xml_header = (
                    '<LMSDataContainerHeader Version="2">'
                    f'<Element Name="{name}">'  # no UniqueID
                    f'{xml_header}'
                    '</Element></LMSDataContainerHeader>'
                )

        elif xml_header.startswith('<LMSDataContainerEnhancedHeader'):
            self.type = LifFileType.LIFEXT

        self.xml_element = ElementTree.fromstring(xml_header)  # noqa: S314
        del xml_header

        element = self.xml_element.find('./Element')
        if element is None:
            if self.type != LifFileType.LIFEXT:
                logger().warning(f'{self!r} Element element not found in XML')
        else:
            self.name = element.attrib.get('Name', self.name)
            self.uuid = element.attrib.get('UniqueID')

        try:
            self.version = int(self.xml_element.attrib['Version'])
        except KeyError:
            if self.type != LifFileType.LOF:
                msg = 'Version attribute not found in XML'
                raise KeyError(msg) from None

        # add memory blocks
        if self.type == LifFileType.LOF:
            # LOF files only contain a single memory block without id.
            # Any id would work.
            # However, try to preserve original id from XML metadata.
            memory = self.xml_element.find('./Element/Memory')
            memblock_id: str | None
            if memory is None:
                # raise Memory element not found in XML
                memblock_id = 'MemBlock_0'
            else:
                memblock_id = memory.get('MemoryBlockID')
                if memblock_id is None:
                    # raise MemoryBlockID attribute not found in XML
                    memblock_id = 'MemBlock_0'

            memblock.id = memblock_id  # LOF memory blocks don't have id
            self.memory_blocks[memblock.id] = memblock

        elif self.type in {LifFileType.LIF, LifFileType.LIFEXT}:
            while True:
                try:
                    memblock = LifMemoryBlock(self)
                except (OSError, LifFileError):
                    break
                self.memory_blocks[memblock.id] = memblock

        elif self.type in {
            LifFileType.XLIF,
            LifFileType.XLEF,
            LifFileType.XLCF,
        }:
            assert element is not None
            if element.find('./Data/Collection') is not None:
                self.type = LifFileType.XLCF
            elif element.find('./Data/Experiment') is not None:
                if self._path.lower().endswith('.xllf') or any(
                    a.text == '__IOManagerFolderV2'
                    for a in element.findall('./Attributes/Attribute')
                ):
                    self.type = LifFileType.XLLF
                else:
                    self.type = LifFileType.XLEF
            memblock = LifMemoryBlock(self)
            self.memory_blocks[memblock.id] = memblock

        else:
            msg = f'unsupported file type={self.type!r}'
            raise ValueError(msg)

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

    @cached_property
    def children(self) -> tuple[LifFile, ...]:
        """Children references in XLEF, XLCF, and XLLF files."""
        dirname = self.dirname
        children: list[LifFile] = []
        for child in self.xml_element.findall('./Element/Children/Reference'):
            filename = child.attrib.get('File')
            if filename is None:
                continue
            filename = os.path.normpath(unquote(filename)).replace('\\', '/')
            filename = os.path.join(dirname, filename)
            if not os.path.exists(filename):
                filename = case_sensitive_path(filename)
            children.append(
                LifFile(
                    filename,
                    memmap=self._memmap,
                    squeeze=self._squeeze,
                    _parent=self,
                )
            )
        return tuple(children)

    @property
    def parent(self) -> LifFile | None:
        """Parent file, if any."""
        return self._parent

    def xml_header(self) -> str:
        """Return XML object description from file."""
        xml: str | bytes
        if self._path and self._fh.closed and os.path.isfile(self._path):
            with open(self._path, 'rb') as fh:
                fh.seek(self._xml_header[0])
                xml = fh.read(self._xml_header[1])
        else:
            # TODO: this fails with closed remote file handles
            xml = bytes(
                self._read_at(self._xml_header[0], self._xml_header[1])
            )
        if self._xml_header[1] < 0:
            return xml.decode(XML_CODEC[xml[:4]])
        return xml.decode('utf-16-le')

    def close(self) -> None:
        """Close file handle and free resources."""
        if self._close:
            for child in self.children:
                child.close()
        for ref in self._open_files:
            with contextlib.suppress(Exception):
                ref.close()
        self._open_files.clear()
        super().close()

    def __enter__(self) -> LifFile:
        return self

    def __str__(self) -> str:
        return indent(
            repr(self),
            f'path: {self._path}',
            f'type: {self.type}',
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

    All attributes are read-only.

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

    _shape_stored: tuple[int, ...] | None

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
        self._shape_stored = None

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

    @property
    def frames(self) -> LifImageFrames:
        """Interface for accessing individual image frames."""
        msg = 'frames property not implemented for this image type'
        raise NotImplementedError(msg)

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
        if self.parent.type != LifFileType.LIFEXT or '/' in dirname:
            return parent.images.find(f'^{dirname}$')

        # LIFEXT root image references image in parent LIF file
        # via MemoryBlockID.
        # The lookup is inefficient but maintaining a reverse mapping
        # of MemoryBlockID to image is not worth for this case only.
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
        if self.parent.type in {LifFileType.LOF, LifFileType.XLIF}:
            # XLIF and LOF files contain one memory block
            if not self.parent.memory_blocks:
                msg = 'no memory blocks found in file'
                raise IndexError(msg)
            return self.parent.memory_blocks[
                next(iter(self.parent.memory_blocks.keys()))
            ]
        memory = self.xml_element.find('./Memory')
        if memory is None:
            msg = 'Memory element not found in XML'
            raise IndexError(msg)
        mbid = memory.get('MemoryBlockID')
        if mbid is None:
            msg = 'MemoryBlockID attribute not found in XML'
            raise IndexError(msg)
        return self.parent.memory_blocks[mbid]

    @property
    def timestamps(self) -> NDArray[numpy.datetime64] | None:
        """Time stamps of frames from TimeStampList XML element, if any."""
        return None

    @property
    def tilescan(self) -> LifTileScanInfo | None:
        """Tile scan information from TileScanInfo XML element, if any."""
        return None

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
        def _get_attr_str(name: str) -> str | None:
            try:
                value = getattr(self, name)
                if callable(value):
                    return None
                return f'{name}: {value!r}'[:160]
            except (NotImplementedError, AttributeError):
                return None

        return indent(
            repr(self),
            *(
                s
                for name in dir(self)
                if not name.startswith('_') and (s := _get_attr_str(name))
            ),
        )


@final
class LifImage(LifImageABC):
    """Regular image.

    Defined by XML Element with Data/Image child.

    """

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
            label = DIMENSION_ID.get(dim_id, '?')
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
                msg = f'invalid {data_type=}'
                raise ValueError(msg)

            if not 0 < resolution <= 64:
                msg = f'invalid {resolution=}'
                raise ValueError(msg)
            if resolution <= 8:
                itemsize = 1
                if dtype == 'f':
                    msg = f'invalid dtype {dtype}{itemsize}'
                    raise ValueError(msg)
            elif resolution <= 16:
                itemsize = 2
            elif resolution <= 32:
                itemsize = 4
            else:
                # resolution <= 64:
                itemsize = 8

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
    def _channel_names(self) -> tuple[str, ...]:
        """Channel names for C or S coordinates."""
        channels = self._channels
        n = len(channels)
        if self.sizes.get('C', 0) > 1 and self.sizes.get('S', 0) > 1:
            return tuple(f'Ch{i}' for i in range(n))
        # build initial names from ChannelProperty/DyeName or ChannelTag
        # fallback, sorted by BytesInc to match _channels order
        channel_elements = sorted(
            self.xml_element.findall(
                './Data/Image/ImageDescription/Channels/ChannelDescription'
            ),
            key=lambda el: int(el.attrib['BytesInc']),
        )
        names = []
        all_generic = True
        for i, ch_el in enumerate(channel_elements):
            tag = int(ch_el.attrib['ChannelTag'])
            if 0 < tag < 4:
                ch_name = ('Red', 'Green', 'Blue')[tag - 1]
                all_generic = False
            else:
                ch_name = f'Ch{i}'
            prop = ch_el.find("ChannelProperty[Key='DyeName']")
            if prop is not None:
                dye = prop.findtext('Value')
                if dye:
                    ch_name = dye.removeprefix('Leica/')
                    all_generic = False
            names.append(ch_name)

        # if all names are generic (Ch0, Ch1, ...) try HardwareSetting sources
        if n > 0 and all_generic:
            hs = self.xml_element.find(
                './Data/Image/Attachment[@Name="HardwareSetting"]'
            )
            if hs is not None:
                # source 1: main ATLConfocalSettingDefinition MultiBand
                acsdef = hs.find('ATLConfocalSettingDefinition')
                if acsdef is not None:
                    mb_names = [
                        mb.attrib['DyeName'].removeprefix('Leica/')
                        for mb in acsdef.findall('.//MultiBand')
                        if mb.attrib.get('DyeName', '')
                    ]
                    if len(mb_names) == n:
                        return tuple(mb_names)

                # source 2: sequential scan per-step
                # each LDM_Block_Sequential_List child is one sequential step;
                # only use if every step activates exactly one channel
                seq = hs.find('LDM_Block_Sequential')
                if seq is not None:
                    step_names: list[str] = []
                    for step_list in seq.findall('LDM_Block_Sequential_List'):
                        for child in step_list:
                            if child.tag == 'ATLConfocalSettingDefinition':
                                step_mb = [
                                    mb.attrib['DyeName']
                                    for mb in child.findall('.//MultiBand')
                                    if mb.attrib.get('DyeName', '')
                                ]
                                if len(step_mb) == 1:
                                    step_names.append(
                                        step_mb[0].removeprefix('Leica/')
                                    )
                    if len(step_names) == n:
                        return tuple(step_names)

        if self._is_bgr:
            names.reverse()
        return tuple(names)

    @cached_property
    def _is_bgr(self) -> bool:
        """Image has BGR channel order."""
        return (
            len(self.memory_block.frames) == 0  # disable for frames
            and self.sizes.get('S', 0) == 3
            and len(self._channels) >= 2
            and self._channels[0].channel_tag == 3  # blue
            and self._channels[1].channel_tag == 2  # green
        )

    @cached_property
    def _lof_reference(self) -> LifFile | None:
        """Cached LOF file if XLIF references single LOF, else None."""
        memblock = self.memory_block
        if (
            memblock.type == LifMemoryBlockType.LOF
            and len(memblock.frames) == 1
        ):
            path = os.path.join(self.parent.dirname, memblock.frames[0].file)
            if not os.path.exists(path):
                path = case_sensitive_path(path)
            lof = LifFile(
                path,
                memmap=self.parent._memmap,
                squeeze=self.parent._squeeze,
            )
            self.parent._open_files.append(lof)
            return lof
        return None

    @cached_property
    def _tif_reference(self) -> TiffFile | None:
        """Cached TiffFile if XLIF references single OME/AIVIA, else None."""
        memblock = self.memory_block
        if len(memblock.frames) == 1 and memblock.type in {
            LifMemoryBlockType.OME,
            LifMemoryBlockType.AIVIA,
        }:
            from tifffile import TiffFile

            path = os.path.join(self.parent.dirname, memblock.frames[0].file)
            if not os.path.exists(path):
                path = case_sensitive_path(path)
            tif = TiffFile(path)
            self.parent._open_files.append(tif)
            return tif
        return None

    @override
    @cached_property
    def dtype(self) -> numpy.dtype[Any]:
        channels = self._channels
        if not channels:
            msg = 'no channels found in image'
            raise ValueError(msg)
        dtype = channels[0].dtype

        if len(channels) > 1 and any(dtype != c.dtype for c in channels):
            msg = (
                'heterogeneous channel data types not supported '
                'by LifImage.asarray; use the frames interface instead. '
                'Please share the file at https://github.com/cgohlke/liffile'
            )
            raise ValueError(msg)

        return dtype

    @override
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

        sizes = {}
        sizes_stored = {}
        stride = self.dtype.itemsize
        ch = 0
        for i, dim in enumerate(reversed(self._dimensions)):
            if squeeze and dim.number_elements < 2:
                continue
            if stride != dim.bytes_inc:
                if dim.bytes_inc % stride == 0:
                    # insert channels where other dimensions are discontiguous
                    # TODO: verify with channel BytesInc
                    size = dim.bytes_inc // stride
                    if i == 0:
                        ax = 'S'
                    else:
                        ax = 'C' if 'C' not in sizes else f'C{ch}'
                        ch += 1
                    sizes[ax] = size
                    assert nchannels % size == 0
                    nchannels //= size
                elif (
                    dim.label == 'Y'
                    and 'X' in sizes
                    and 'S' in sizes
                    and dim.bytes_inc % (sizes['S'] * self.dtype.itemsize) == 0
                ):
                    # account for stride-aligned RGB rows
                    size = dim.bytes_inc // (sizes['S'] * self.dtype.itemsize)
                    sizes_stored['X'] = size
                    assert sizes_stored['X'] > sizes['X']
                else:
                    msg = (
                        f'{stride=} % {dim.bytes_inc=} '
                        f'== {dim.bytes_inc % stride} != 0'
                    )
                    raise ValueError(msg)
            sizes[dim.label] = dim.number_elements
            stride = dim.number_elements * dim.bytes_inc
        if nchannels > 1:
            ax = 'C' if 'C' not in sizes else f'C{ch}'
            sizes[ax] = nchannels

        if sizes_stored:
            self._shape_stored = tuple(
                sizes_stored.get(dim, size)
                for dim, size in reversed(sizes.items())
            )
        return dict(reversed(list(sizes.items())))

    @override
    @cached_property
    def coords(self) -> dict[str, NDArray[Any]]:
        squeeze = self.parent._squeeze
        coords = {}
        for dim in self._dimensions:
            if squeeze and dim.number_elements == 1:
                continue
            if dim.length == 0 and dim.number_elements > 1:
                continue
            coord = numpy.linspace(
                dim.origin,
                dim.origin + dim.length,
                dim.number_elements,
                endpoint=True,
            )
            if dim.label in {'M', 'N'}:
                coord = numpy.astype(coord, numpy.intp)
            coords[dim.label] = coord
        channel_names = self._channel_names
        sizes = self.sizes
        nc = sizes.get('C')
        if nc and nc == len(channel_names):
            coords['C'] = numpy.array(channel_names)
        ns = sizes.get('S')
        if ns and ns == len(channel_names):
            coords['S'] = numpy.array(channel_names)
        return coords

    @override
    @cached_property
    def attrs(self) -> dict[str, Any]:
        path = self.path
        if self.parent.type == LifFileType.LIF:
            path = self.parent.name + '/' + path
        attrs = {
            'filepath': self.parent.filepath,
            'name': self.name,
            'path': path,
            'UniqueID': self.uuid,
        }
        # image_description = self.xml_element.find(
        #     './Data/Image/ImageDescription'
        # )
        # if image_description is not None:
        #     attrs['ImageDescription'] = xml2dict(image_description).get(
        #         'ImageDescription', {}
        #     )
        attrs.update(
            (attach.attrib['Name'], xml2dict(attach)['Attachment'])
            for attach in self.xml_element.findall('./Data/Image/Attachment')
        )
        return attrs

    @cached_property
    def timestamps(self) -> NDArray[numpy.datetime64] | None:
        timestamp = self.xml_element.find('./Data/Image/TimeStampList')
        if timestamp is None:
            return None
        timestamps: Any
        if timestamp.find('./TimeStamp') is not None:
            # LAS < 3.1
            timestamp_elements = timestamp.findall('./TimeStamp')
            high_integers = numpy.empty(
                len(timestamp_elements), dtype=numpy.uint64
            )
            low_integers = numpy.empty(
                len(timestamp_elements), dtype=numpy.uint32
            )
            for i, ts in enumerate(timestamp_elements):
                high_integers[i] = int(ts.attrib['HighInteger'])
                low_integers[i] = int(ts.attrib['LowInteger'])
            timestamps = high_integers << 32
            timestamps += low_integers
        elif timestamp.text is not None:
            # LAS >= 3.1
            timestamps = numpy.fromiter(
                (int(x, 16) for x in timestamp.text.split()),
                dtype=numpy.uint64,
            )
        else:
            return None
        # FILETIME to POSIX
        timestamps -= 116444736000000000
        timestamps //= 10000
        return timestamps.astype(  # type: ignore[no-any-return]
            'datetime64[ms]'
        )

    @cached_property
    def tilescan(self) -> LifTileScanInfo | None:
        tilescaninfo = self.xml_element.find(
            './Data/Image/Attachment[@Name="TileScanInfo"]'
        )
        if tilescaninfo is None:
            return None
        tiles = tilescaninfo.findall('./Tile')
        if not tiles:
            return None
        data = numpy.zeros(
            len(tiles),
            dtype=numpy.dtype(
                [
                    ('field_y', numpy.int32),
                    ('field_x', numpy.int32),
                    ('pos_z', numpy.float64),
                    ('pos_y', numpy.float64),
                    ('pos_x', numpy.float64),
                ]
            ),
        )
        for i, tile in enumerate(tiles):
            attr = tile.attrib
            data[i] = (
                int(attr.get('FieldY', '0')),
                int(attr.get('FieldX', '0')),
                float(attr.get('PosZ', '0')),
                float(attr.get('PosY', '0')),
                float(attr.get('PosX', '0')),
            )
        return LifTileScanInfo(
            bool(int(tilescaninfo.attrib.get('FlipX', '0'))),
            bool(int(tilescaninfo.attrib.get('FlipY', '0'))),
            bool(int(tilescaninfo.attrib.get('SwapXY', '0'))),
            data,
        )

    def frame(
        self,
        *,
        out: OutputType = None,
        **indices: int,
    ) -> NDArray[Any]:
        """Return single frame from image.

        A frame consists of the innermost two contiguous dimensions
        (typically Y and X) and an optional sample dimension (S for RGB).

        Parameters:
            out:
                Specifies where to copy frame data.
                If ``None``, create a new NumPy array in main memory.
                If ``'memmap'``, create a memory-mapped array in a
                temporary file.
                If a ``numpy.ndarray``, a writable, initialized array
                of compatible shape and dtype.
                If a ``file name`` or ``open file``, create a
                memory-mapped array in the specified file.
            **indices:
                Global dimension indices using case-sensitive dimension codes.
                Unspecified dimensions default to index 0.
                Example: ``C=1, Z=2, T=0`` for channel 1, Z-plane 2, time 0.

        Returns:
            :
                Frame data as numpy array.

        Raises:
            KeyError: If unknown dimension specified.
            IndexError: If index is out of bounds.

        """
        return self.frames._read_frame(out=out, **indices)

    @cached_property
    def frames(self) -> LifImageFrames:
        """Interface for accessing individual image frames.

        The :py:class:`LifImageFrames` instance provides a mapping and
        sequence-like interface for memory-efficient, frame-level access
        to higher dimensional image data with per-dimension selection.

        Examples:
            Access single frame using global indices::

                frame = image.frames[0]  # first frame
                frame = image.frame(C=1, Z=2, T=0)  # specific indices

            Create selection and iterate::

                selected = image.frames(C=1, Z=slice(1, 3))
                for index, frame in selected.items():
                    process(frame)

        """
        return LifImageFrames(self)

    @override
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

        Notes:
            For advanced use cases, use the :py:attr:`frames` interface,
            which supports per-dimension selections, heterogeneous channel
            data types, and discontiguous storage.

        """
        if self._shape_stored is None:
            data = self.memory_block.read_array(
                self.shape, self.dtype, mode=mode, out=out
            )
        else:
            # shape_stored differs from shape (e.g., stride-aligned rows)
            # out must match _shape_stored or be None
            data = self.memory_block.read_array(
                self._shape_stored, self.dtype, mode=mode, out=out
            )
            data = data[tuple(slice(size) for size in self.shape)]
        if self._is_bgr:
            # BGR to RGB
            if not data.flags.writeable:
                data = data[..., ::-1].copy()
            else:
                data[:] = data[..., ::-1]
        return data


@final
class LifFlimImage(LifImageABC):
    """FLIM/TCSPC histogram image.

    Defined by XML Element with Data/SingleMoleculeDetection child.

    """

    @override
    @cached_property
    def dtype(self) -> numpy.dtype[Any]:
        return numpy.dtype(numpy.uint16)

    @override
    @cached_property
    def sizes(self) -> dict[str, int]:
        sizes = {'H': self.number_bins_in_period}

        dims = self.xml_element.find(
            './Data/SingleMoleculeDetection/Dataset/RawData/Dimensions'
        )
        if dims is None:
            msg = 'Dimensions element not found in XML'
            raise ValueError(msg)

        for dimid, size in zip(
            dims.findall('Dimension/DimensionIdentifier'),
            dims.findall('Dimension/Size'),
            strict=True,
        ):
            if dimid.text is None or size.text is None or int(size.text) <= 1:
                continue
            name = {'M': 'A', 'S': 'M'}.get(dimid.text, dimid.text)
            sizes[name] = int(size.text)

        return dict(reversed(list(sizes.items())))

    @override
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

    @override
    @cached_property
    def attrs(self) -> dict[str, Any]:
        rawdata = self.xml_element.find(
            './Data/SingleMoleculeDetection/Dataset/RawData'
        )
        if rawdata is None:
            msg = 'RawData element not found in XML'
            raise ValueError(msg)
        attrs = xml2dict(rawdata, exclude={'Dimensions', 'Channels'})
        return {
            'filepath': self.parent.filepath,
            'name': self.name,
            'path': self.parent.name + '/' + self.path,
            'UniqueID': self.uuid,
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
        frequency = float(attrs['LaserPulseFrequency'])
        clock_period = float(attrs['ClockPeriod'])
        if frequency == 0.0 or clock_period == 0.0:
            return 1
        return max(1, math.floor(1.0 / frequency / clock_period))

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

    @override
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
        fmt = self.attrs['RawData']['Format']
        msg = f'format={fmt!r} is patent-pending'
        raise NotImplementedError(msg)


@final
class LifImageFrames:
    """Interface for accessing individual image frames in LifImage.

    A mapping and sequence-like interface providing memory-efficient,
    frame-level access to higher dimensional image data with per-dimension
    selection.

    A frame consists of the innermost two contiguous dimensions of the image
    (typically Y and X) and an optional sample dimension (S for RGB).

    Instances are usually obtained via the :py:attr:`LifImage.frames` property.

    Parameters:
        image:
            Parent LifImage instance.
        **selection:
            Per-dimension selection using case-sensitive codes.

            - ``int``: Fixed index (dimension not iterated).
            - ``slice``: Range of indices to iterate.
            - ``Sequence[int]``: Specific indices to iterate.
            - ``None``: Iterate all indices.

    Raises:
        KeyError: If unknown dimension specified.
        ValueError: If frame dimension (for example, Y, X, S) specified.

    """

    _image: LifImage
    _selection: SelectionType

    def __init__(
        self,
        image: LifImage,
        /,
        **selection: SelectionValue,
    ) -> None:
        self._image = image
        self._selection = selection

        if not selection:
            return

        for key in selection:
            if key not in image.sizes:
                msg = f'unknown dimension {key!r}'
                raise KeyError(msg)

    def __call__(
        self,
        **selection: SelectionValue,
    ) -> LifImageFrames:
        """Create new instance with selection.

        Parameters:
            **selection:
                Per-dimension selection using case-sensitive codes.

                - ``int``: Fixed index (dimension not iterated).
                - ``slice``: Range of indices to iterate.
                - ``Sequence[int]``: Specific indices to iterate.
                - ``None``: Iterate all indices.

        Returns:
            New LifImageFrames instance.

        Raises:
            ValueError: If called on instance with existing selection.

        """
        if not selection:
            return self

        if self._selection:
            msg = 'cannot chain selections; call on image.frames instead'
            raise ValueError(msg)

        return LifImageFrames(self._image, **selection)

    @cached_property
    def _info(self) -> LifImageFramesInfo:
        """Private cached information used repeatedly."""
        image = self._image
        frame_dims = set(self.frame_sizes.keys())

        # validate selection keys now that frame_sizes is computed
        for key in self._selection:
            if key in frame_dims:
                msg = (
                    f'cannot select frame dimension {key!r}; '
                    f'frame dimensions {tuple(frame_dims)} are fixed'
                )
                raise ValueError(msg)

        iter_dims: list[str] = []
        iter_sizes: list[int] = []
        iter_ranges: list[Sequence[int]] = []

        # add unspecified non-frame dimensions in natural order
        for dim in image.dims:
            if dim in self._selection or dim in frame_dims:
                continue
            size = image.sizes[dim]
            iter_dims.append(dim)
            iter_sizes.append(size)
            iter_ranges.append(range(size))

        # add specified non-frame dimensions in order of specification
        for dim, sel in self._selection.items():
            # No need to check frame_dims - already validated above

            size = image.sizes[dim]
            match sel:
                case None:
                    # iterate all
                    iter_sizes.append(size)
                    iter_ranges.append(range(size))
                case _ if isinstance(sel, (int, numpy.integer)):
                    # fixed index
                    if not 0 <= sel < size:
                        msg = (
                            f'index {sel} out of bounds '
                            f'for dimension {dim!r} with size {size}'
                        )
                        raise IndexError(msg)
                    iter_sizes.append(1)
                    iter_ranges.append((int(sel),))
                case slice():
                    r = range(*sel.indices(size))
                    iter_sizes.append(len(r))
                    iter_ranges.append(r)
                case _:
                    # sequence of indices
                    for idx in sel:
                        if not 0 <= idx < size:
                            msg = (
                                f'index {idx} out of bounds '
                                f'for dimension {dim!r} with size {size}'
                            )
                            raise IndexError(msg)
                    iter_sizes.append(len(sel))
                    iter_ranges.append(sel)

            iter_dims.append(dim)

        full_dims: tuple[str, ...] | None = None
        full_ranges: tuple[Sequence[int], ...] | None = None

        # squeeze out length-1 dimensions if enabled
        if image.parent._squeeze:
            squeezed = [
                (d, s, r)
                for d, s, r in zip(
                    iter_dims, iter_sizes, iter_ranges, strict=True
                )
                if s > 1
            ]
            if len(squeezed) < len(iter_dims):
                # store full dimensions for unsqueezing in __getitem__
                full_dims = tuple(iter_dims)
                full_ranges = tuple(iter_ranges)
                if squeezed:
                    dims_tuple, sizes_tuple, ranges_tuple = zip(
                        *squeezed, strict=True
                    )
                    iter_dims = list(dims_tuple)
                    iter_sizes = list(sizes_tuple)
                    iter_ranges = list(ranges_tuple)
                else:
                    # all dimensions squeezed out
                    iter_dims, iter_sizes, iter_ranges = [], [], []

        sizes = dict(zip(iter_dims, iter_sizes, strict=True))
        sizes.update(self.frame_sizes)

        return LifImageFramesInfo(
            length=product(iter_sizes),
            dims=tuple(iter_dims),
            shape=tuple(iter_sizes),
            sizes=sizes,
            ranges=tuple(iter_ranges),
            full_dims=full_dims,
            full_ranges=full_ranges,
        )

    def _read_frame(
        self,
        *,
        out: OutputType = None,
        **indices: int,
    ) -> NDArray[Any]:
        """Read single frame using global dimension indices.

        This is a private method that reads frame data from the image
        using absolute/global dimension indices.

        Parameters:
            out:
                Output array or ``'memmap'``.
            **indices:
                Global dimension indices (unspecified default to 0).

        Returns:
            Frame data as numpy array.

        """
        image = self._image
        memblock = image.memory_block

        # if XLIF references single LOF, delegate to LOF's frame
        lof_ref = image._lof_reference
        if lof_ref is not None:
            return lof_ref.images[0].frames._read_frame(out=out, **indices)

        tif_ref = image._tif_reference
        if tif_ref is not None:
            # calculate global linear frame index
            frame_dims = set(self.frame_sizes.keys())
            iter_dims = [d for d in image.dims if d not in frame_dims]
            if iter_dims:
                nd_index = tuple(indices.get(d, 0) for d in iter_dims)
                shape = tuple(image.sizes[d] for d in iter_dims)
                linear_index = int(numpy.ravel_multi_index(nd_index, shape))
            else:
                linear_index = 0
            data = tif_ref.pages[linear_index].asarray(out=out)
            if self.dtype == numpy.float16:
                # float16 data are stored as uint16 in TIFF
                data = data.view(numpy.float16)
            return data

        # validate indices
        for key, value in indices.items():
            if key not in image.sizes:
                msg = f'unknown dimension {key!r}'
                raise KeyError(msg)
            if not 0 <= value < image.sizes[key]:
                msg = (
                    f'index {value} out of bounds '
                    f'for dimension {key!r} with size {image.sizes[key]}'
                )
                raise IndexError(msg)

        # calculate byte offset from dimension indices
        offset = 0
        frame_dims = set(self.frame_sizes.keys())
        for dim in image._dimensions:
            if dim.label in frame_dims:
                continue
            idx = indices.get(dim.label, 0)
            offset += idx * dim.bytes_inc

        # determine channel and its dtype
        channel_idx = indices.get('C', 0)
        if image._channels:
            # when S is in frame_dims, channels are grouped by C
            # with S samples per C, so index is C * S
            if 'S' in frame_dims:
                channel_idx *= image.sizes.get('S', 1)
            channel = image._channels[channel_idx]
            offset += channel.bytes_inc
            dtype = channel.dtype
        else:
            dtype = image.dtype

        # calculate frame size in bytes
        frame_shape = self.frame_shape
        frame_nbytes = product(frame_shape) * dtype.itemsize

        # read frame from memory block frames (XLIF with external files)
        if memblock.frames:
            # find frame containing the calculated offset
            for frame in memblock.frames:
                frame_start = frame.offset
                frame_end = frame.offset + frame.size
                if frame_start <= offset < frame_end:
                    # check if entire requested data fits within this frame
                    if offset + frame_nbytes <= frame_end:
                        # WARNING: this may read more data than needed
                        # if external file contains multiple frames.
                        # However, LOF and multi-page TIFF files are
                        # special-cased above.
                        data = frame.imread(image.parent.dirname)
                        data = data.reshape(-1).view(numpy.uint8)
                        local_offset = offset - frame_start
                        data = data[local_offset : local_offset + frame_nbytes]
                        data = data.view(dtype).reshape(frame_shape)
                        if out is None:
                            return data.copy()
                        result = create_output(out, frame_shape, dtype)
                        result[:] = data
                        return result
                    # requested data spans multiple external files
                    break
            # offset not found or data spans multiple files
            msg = 'frame not supported for this XLIF layout'
            raise NotImplementedError(msg)

        # read frame directly from LIF/LOF file
        if memblock.offset < 0:
            msg = 'memory block has no offset and no frames'
            raise ValueError(msg)

        data = image.parent._read_array(
            memblock.offset + offset, product(frame_shape), dtype
        )
        result = create_output(out, frame_shape, dtype)
        result[:] = data.reshape(frame_shape)
        if image._is_bgr:
            result[:] = result[..., ::-1]  # BGR to RGB
        return result

    @cached_property
    def frame_sizes(self) -> dict[str, int]:
        """Dimension sizes of single frame."""
        # For most files, a simple approach would work::
        #
        #     dims = list(image.sizes.keys())
        #     frame_dims = dims[-3:] if dims[-1] == 'S' else dims[-2:]
        #
        # However, this implementation ensures correctness for:
        #
        # * XLIF files referencing external data
        # * Stride-aligned images
        # * Files with unusual memory layouts
        #
        # The function can in principle return:
        #
        # * 3 dimensions: {Y, X, S} (typical RGB)
        # * 2 dimensions: {Y, X} (typical grayscale), {T, X}, {Z, X}, or {X, S}
        #   (stride-aligned with Y excluded)
        # * 1 dimension: {X} (severe layout issues)
        # * 0 dimensions: {} (no contiguous data or extreme constraints)

        image = self._image
        # only consider dimensions present in sizes (not squeezed)
        dims_in_sizes = [
            dim for dim in image._dimensions if dim.label in image.sizes
        ]
        if not dims_in_sizes:
            return {}

        # if XLIF references single LOF, delegate to LOF's frame structure
        if image._lof_reference is not None:
            return image._lof_reference.images[0].frames.frame_sizes

        memblock = image.memory_block

        # sort by bytes_inc ascending to get inner-to-outer order
        dims_ascending = sorted(dims_in_sizes, key=lambda d: d.bytes_inc)

        frame_labels: list[str] = []
        expected_stride = image.dtype.itemsize

        for dim in dims_ascending:
            if dim.bytes_inc == expected_stride:
                # contiguous with previous, include in frame
                frame_labels.append(dim.label)
                expected_stride = dim.bytes_inc * dim.number_elements
            elif (
                dim.bytes_inc > expected_stride
                and dim.bytes_inc % expected_stride == 0
            ):
                # gap may be filled by sample dimension (RGB)
                gap_size = dim.bytes_inc // expected_stride
                if (
                    'S' in image.sizes
                    and image.sizes['S'] == gap_size
                    and 'S' not in frame_labels
                ):
                    frame_labels.append('S')
                    expected_stride = dim.bytes_inc
                    frame_labels.append(dim.label)
                    expected_stride = dim.bytes_inc * dim.number_elements
                else:
                    # true discontinuity, frame ends
                    break
            elif (
                dim.label == 'Y'
                and 'X' in frame_labels
                and 'S' in frame_labels
                and dim.bytes_inc % (image.sizes['S'] * image.dtype.itemsize)
                == 0
            ):
                # account for stride-aligned RGB rows (padding at end of rows)
                frame_labels.append(dim.label)
                expected_stride = dim.bytes_inc * dim.number_elements
            else:
                # discontinuity
                break

        # limit frame to 2 spatial dimensions plus optional S
        # count non-S dimensions
        spatial_count = sum(1 for d in frame_labels if d != 'S')
        if spatial_count > 2:
            # keep only innermost 2 spatial dimensions (+ S if present)
            # frame_labels is ordered inner-to-outer, so keep first entries
            kept: list[str] = []
            spatial_kept = 0
            for label in frame_labels:
                if label == 'S':
                    kept.append(label)
                elif spatial_kept < 2:
                    kept.append(label)
                    spatial_kept += 1
                else:
                    break
            frame_labels = kept

        # check if external frames constrain the frame size
        if memblock.frames:
            # find smallest external frame size
            min_frame_size = min(frame.size for frame in memblock.frames)
            # remove outer dimensions until frame fits in external frame
            # frame_labels is inner-to-outer, so remove from end
            while frame_labels:
                frame_nbytes = (
                    product(image.sizes[d] for d in frame_labels)
                    * image.dtype.itemsize
                )
                if frame_nbytes <= min_frame_size:
                    break
                frame_labels.pop()

        frame_set = set(frame_labels)
        # return in same order as image.sizes
        return {
            dim: size for dim, size in image.sizes.items() if dim in frame_set
        }

    @property
    def frame_shape(self) -> tuple[int, ...]:
        """Shape of single frame."""
        return tuple(self.frame_sizes.values())

    @property
    def frame_dims(self) -> tuple[str, ...]:
        """Dimension names of single frame."""
        return tuple(self.frame_sizes.keys())

    @property
    def sizes(self) -> dict[str, int]:
        """Map dimension names to lengths.

        Including selected and frame dimensions.

        """
        return self._info.sizes

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape including selected and frame dimensions."""
        return tuple(self._info.sizes.values())

    @property
    def dims(self) -> tuple[str, ...]:
        """Dimension names including selected and frame dimensions."""
        return tuple(self._info.sizes.keys())

    @property
    def ndim(self) -> int:
        """Number of dimensions including selected and frame dimensions."""
        return len(self._info.sizes)

    @cached_property
    def dtype(self) -> numpy.dtype[Any]:
        """Data type resulting from NumPy type promotion rules."""
        channels = self._image._channels
        if not channels:
            msg = 'no channels found in image'
            raise ValueError(msg)
        return numpy.result_type(*(c.dtype for c in channels))

    @property
    def coords(self) -> dict[str, NDArray[Any]]:
        """Physical coordinates for selected and frame dimensions."""
        image_coords = self._image.coords

        result = {}
        for dim in self._info.dims:
            if dim in image_coords:
                coord_array = image_coords[dim]
                # get indices for this dimension in selection
                if dim in self._selection:
                    sel = self._selection[dim]
                    match sel:
                        case None:
                            result[dim] = coord_array
                        case _ if isinstance(sel, (int, numpy.integer)):
                            result[dim] = coord_array[sel : sel + 1]
                        case slice():
                            result[dim] = coord_array[sel]
                        case _:
                            result[dim] = coord_array[list(sel)]
                else:
                    result[dim] = coord_array

        # add frame dimension coordinates
        for dim in self.frame_sizes:
            if dim in image_coords:
                result[dim] = image_coords[dim]

        return result

    def keys(self) -> Iterator[tuple[int, ...]]:
        """Return iterator over ND indices (tuples).

        Yields:
            ND index tuples for each frame in the selection.

        """
        yield from itertools.product(
            *(range(size) for size in self._info.shape)
        )

    def values(self) -> Iterator[NDArray[Any]]:
        """Return iterator over frames.

        Equivalent to iterating over the sequence directly.

        Yields:
            Frame data as numpy arrays.

        """
        return iter(self)

    def items(self) -> Iterator[tuple[tuple[int, ...], NDArray[Any]]]:
        """Return iterator over (ND index, frame) pairs.

        Yields:
            Tuples of (index, frame) where index is an ND tuple and
            frame is the corresponding numpy array.

        """
        for key in self.keys():
            yield key, self[key]

    def get(
        self,
        key: int | tuple[int, ...],
        default: NDArray[Any] | None = None,
    ) -> NDArray[Any] | None:
        """Return frame by local index, with default.

        Parameters:
            key:
                Linear index (int) or ND index (tuple).
            default:
                Value to return if key not found.

        Returns:
            Frame data or default.

        """
        try:
            return self[key]
        except (IndexError, KeyError, TypeError):
            return default

    def asarray(self, *, out: OutputType = None) -> NDArray[Any]:
        """Return selected frames as single array.

        Parameters:
            out:
                Output array or ``'memmap'``.

        Returns:
            Array with :py:attr:`shape` and :py:attr:`dtype`.

        """
        if not self.shape:
            return numpy.array([], self.dtype)
        result = create_output(out, self.shape, self.dtype)
        for index, frame in self.items():
            result[index] = frame
        return result

    def asxarray(self, **kwargs: Any) -> DataArray:
        """Return selected frames as xarray.

        Parameters:
            **kwargs: Optional arguments to :py:meth:`asarray`.

        Returns:
            :
                Image data and metadata of selected frames as xarray DataArray.

        """
        from xarray import DataArray

        return DataArray(
            self.asarray(**kwargs),
            coords=self.coords,
            dims=self.dims,
            name=self._image.name,
            attrs=self._image.attrs,
        )

    def unravel_index(
        self,
        linear_index: int,
        /,
        *,
        global_: bool = False,
    ) -> tuple[int, ...]:
        """Convert linear index to ND index.

        Parameters:
            linear_index:
                Linear index (0 to len-1).
            global_:
                If ``True``, return global (absolute) indices.
                If ``False``, return local (selection-relative) indices.

        Returns:
            ND index as tuple, excluding frame dimensions.

        Raises:
            IndexError: If linear_index is out of bounds.

        """
        info = self._info

        if not 0 <= linear_index < info.length:
            msg = (
                f'linear index {linear_index} out of bounds '
                f'for length {info.length}'
            )
            raise IndexError(msg)

        # convert to local ND index
        local_nd = []
        remaining = linear_index
        for size in reversed(info.shape):
            local_nd.append(remaining % size)
            remaining //= size
        local_nd.reverse()

        if not global_:
            return tuple(local_nd)

        # convert to global ND index
        global_nd = []
        for local_idx, range_seq in zip(local_nd, info.ranges, strict=True):
            if isinstance(range_seq, range):
                global_nd.append(range_seq[local_idx])
            else:
                global_nd.append(int(range_seq[local_idx]))

        return tuple(global_nd)

    def ravel_multi_index(
        self,
        nd_index: tuple[int, ...],
        /,
        *,
        global_: bool = False,
    ) -> int:
        """Convert ND index to linear index.

        Parameters:
            nd_index:
                ND index as tuple, excluding frame dimensions.
            global_:
                If ``True``, nd_index contains global (absolute) indices.
                If ``False``, nd_index contains local (selection-relative)
                indices.

        Returns:
            Linear index.

        Raises:
            ValueError: If nd_index has wrong length.
            IndexError: If any index is out of bounds.

        """
        info = self._info

        if len(nd_index) != len(info.dims):
            msg = (
                f'nd_index length {len(nd_index)} does not match '
                f'number of iteration dimensions {len(info.dims)}'
            )
            raise ValueError(msg)

        local_nd = nd_index
        if global_:
            # convert global to local
            local_nd_list = []
            for global_idx, range_seq in zip(
                nd_index, info.ranges, strict=True
            ):
                if isinstance(range_seq, range):
                    try:
                        local_idx = range_seq.index(global_idx)
                    except ValueError:
                        msg = (
                            f'global index {global_idx} '
                            f'not in range {range_seq}'
                        )
                        raise IndexError(msg) from None
                else:
                    try:
                        local_idx = next(
                            i
                            for i, val in enumerate(range_seq)
                            if val == global_idx
                        )
                    except StopIteration:
                        msg = (
                            f'global index {global_idx} '
                            f'not in sequence {range_seq}'
                        )
                        raise IndexError(msg) from None
                local_nd_list.append(local_idx)
            local_nd = tuple(local_nd_list)

        # validate bounds
        for idx, size in zip(local_nd, info.shape, strict=True):
            if not 0 <= idx < size:
                msg = f'index {idx} out of bounds for size {size}'
                raise IndexError(msg)

        # convert to linear
        linear = 0
        for idx, size in zip(local_nd, info.shape, strict=True):
            linear = linear * size + idx

        return linear

    def __getitem__(self, key: int | tuple[int, ...], /) -> NDArray[Any]:
        """Get frame by local index.

        Parameters:
            key:
                Linear index (int) or ND index (tuple of int).

        Returns:
            Frame data as numpy array.

        Raises:
            IndexError: If key is out of bounds.
            TypeError: If key has wrong type.

        """
        info = self._info

        if isinstance(key, (int, numpy.integer)):
            # convert linear to ND local
            nd_local = self.unravel_index(int(key), global_=False)
        elif isinstance(key, tuple):
            nd_local = tuple(int(i) for i in key)
            if len(nd_local) != len(info.dims):
                msg = (
                    f'ND index length {len(nd_local)} does not match '
                    f'number of iteration dimensions {len(info.dims)}'
                )
                raise IndexError(msg)
        else:
            msg = f'indices must be int or tuple, not {type(key).__name__}'
            raise TypeError(msg)

        # convert local ND to global ND directly
        nd_global = []
        for local_idx, range_seq in zip(nd_local, info.ranges, strict=True):
            if isinstance(range_seq, range):
                nd_global.append(range_seq[local_idx])
            else:
                nd_global.append(int(range_seq[local_idx]))

        # build global indices dict
        global_indices = dict(zip(info.dims, nd_global, strict=True))

        # unsqueeze if necessary (restore length-1 dimensions)
        if info.full_dims is not None:
            assert info.full_ranges is not None
            full_global_indices = {}
            for dim, range_seq in zip(
                info.full_dims, info.full_ranges, strict=True
            ):
                if dim in global_indices:
                    full_global_indices[dim] = global_indices[dim]
                else:
                    # this was a squeezed dimension, use its single value
                    full_global_indices[dim] = next(iter(range_seq))
            global_indices = full_global_indices

        return self._read_frame(out=None, **global_indices)

    def __len__(self) -> int:
        """Number of frames in selection."""
        return self._info.length

    def __iter__(self) -> Iterator[NDArray[Any]]:
        """Iterate over selected frames."""
        yield from (self[key] for key in self.keys())

    def __repr__(self) -> str:
        info = self._info
        frame_shape = self.frame_shape
        if info.dims:
            iter_pairs = ', '.join(
                f'{d}: {s}' for d, s in zip(info.dims, info.shape, strict=True)
            )
            iter_str = f'({iter_pairs})'
            return (
                f'<LifImageFrames {self._image.name!r} '
                f'{iter_str} x {frame_shape}>'
            )
        return f'<LifImageFrames {self._image.name!r} {frame_shape}>'


@dataclass(slots=True, frozen=True)
class LifImageFramesInfo:
    """Internal information for LifImageFrames."""

    length: int
    """Number of frames."""

    dims: tuple[str, ...]
    """Post-squeeze dimension names excluding frame."""

    shape: tuple[int, ...]
    """Post-squeeze dimension sizes excluding frame."""

    sizes: dict[str, int]
    """Dimension names and sizes including frame."""

    ranges: tuple[Sequence[int], ...]
    """Post-squeeze ranges for each dimension excluding frame."""

    full_dims: tuple[str, ...] | None = None
    """Pre-squeeze dimension names, if squeezing removed dimensions."""

    full_ranges: tuple[Sequence[int], ...] | None = None
    """Pre-squeeze ranges, if squeezing removed dimensions."""


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

        if parent.type not in {
            LifFileType.XLEF,
            LifFileType.XLCF,
            LifFileType.XLLF,
        }:
            keepbase = parent.type == LifFileType.LIFEXT
            for path, element in self._image_iter(parent.xml_element):
                path_ = path if keepbase else path.split('/', 1)[-1]
                if element.find('./Data/SingleMoleculeDetection') is None:
                    image = LifImage(parent, element, path_)
                else:
                    image = LifFlimImage(parent, element, path_)
                # LAS X usually refuses to write images with duplicate paths.
                # However, paths from XML may in principle collide, hence the
                # renaming logic, which is opaque to users.
                if path_ in self._images:
                    for i in range(1, 1000):
                        # this loop generates readable keys;
                        # remove if performance becomes an issue
                        new_path = f'{path_}~{i:03}'
                        if new_path not in self._images:
                            path_ = new_path
                            break
                    else:
                        # fall back to uuid;
                        # image.uuid cannot be used because it may be None
                        path_ = f'{path_}_{uuid.uuid4().hex}'
                self._images[path_] = image

        for child in parent.children:
            for image in child.images:
                path = image.path
                if parent.type not in {LifFileType.XLEF, LifFileType.XLLF}:
                    path = f'{parent.name}/{path}'
                self._images[path] = image
                image.path = path

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
            path = name if base_path == '' else f'{base_path}/{name}'
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
        self,
        key: str,
        /,
        *,
        attr: str = 'path',
        flags: int = re.IGNORECASE,
        default: Any = None,
    ) -> LifImageABC | None:
        """Return first image with matching attribute pattern, if any.

        Parameters:
            key:
                Regular expression pattern to match str of LifImage attribute.
            attr:
                LifImage attribute to match against (default: ``'path'``).
            flags:
                Regular expression flags.
            default:
                Value to return if no image with matching attribute found.

        """
        pattern = re.compile(key, flags=flags)
        for image in self._images.values():
            value = str(getattr(image, attr, ''))
            if pattern.search(value) is not None:
                return image
        return default  # type: ignore[no-any-return]

    def findall(
        self,
        key: str,
        /,
        *,
        attr: str = 'path',
        flags: int = re.IGNORECASE,
    ) -> tuple[LifImageABC, ...]:
        """Return all images with matching attribute pattern.

        Parameters:
            key:
                Regular expression pattern to match str of LifImage attribute.
            attr:
                LifImage attribute to match against (default: ``'path'``).
            flags:
                Regular expression flags.

        """
        pattern = re.compile(key, flags=flags)
        images = []
        for image in self._images.values():
            value = str(getattr(image, attr, ''))
            if pattern.search(value) is not None:
                images.append(image)
        return tuple(images)

    @override
    def __getitem__(  # type: ignore[override]
        self,
        key: int | str,
        /,
    ) -> LifImageABC:
        """Return image at index or first image with path matching pattern.

        Raises:
            IndexError: if integer index out of range.
            KeyError: if no image with matching path pattern found.

        """
        if isinstance(key, int):
            index = key
            try:
                key = tuple(self._images.keys())[index]
            except IndexError:
                msg = f'image {index=} out of range'
                raise IndexError(msg) from None
            return self._images[key]
        if key in self._images:
            return self._images[key]
        pattern = re.compile(key, flags=re.IGNORECASE)
        for image in self._images.values():
            if pattern.search(image.path) is not None:
                return image
        msg = f'image {key!r} not found'
        raise KeyError(msg)

    @override
    def __len__(self) -> int:
        return len(self._images)

    @override
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


class LifMemoryBlockType(enum.IntEnum):
    """Leica image file memory block type."""

    UNKNOWN = -1
    """Unknown memory block type."""

    MEM = 0
    """Memory block embedded in LIF."""

    LOF = 1
    """Memory block in single LOF file."""

    TIF = 2
    """Memory blocks in TIF files."""

    OME = 3
    """Memory blocks in OME TIF files."""

    AIVIA = 4
    """Memory blocks in Aivia TIF files."""

    JPG = 5
    """Memory blocks in JPG files."""

    PNG = 6
    """Memory blocks in PNG files."""

    BMP = 7
    """Memory blocks in BMP files."""


@final
class LifMemoryBlock:
    """Object memory block.

    Parameters:
        parent: Underlying LIF file.

    """

    __slots__ = ('parent', 'type', 'id', 'offset', 'size', 'frames')

    parent: LifFile
    """Underlying LIF file."""

    type: LifMemoryBlockType
    """Memory block type."""

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
        self.type = LifMemoryBlockType.MEM
        self.id = ''
        self.offset = -1
        self.size = 0
        self.frames = ()

        if parent.type in {
            LifFileType.XLEF,
            LifFileType.XLCF,
            LifFileType.XLLF,
        }:
            return

        if parent.type == LifFileType.XLIF:
            memory = parent.xml_element.find('./Element/Memory')
            if memory is None:
                msg = 'Memory element not found in XML'
                raise ValueError(msg)
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
            self.type = LifMemoryBlockType.UNKNOWN
            if frames:
                file = self.frames[0].file.lower()
                if file.endswith('.lof'):
                    self.type = LifMemoryBlockType.LOF
                elif file.endswith('.ome.tif'):
                    self.type = LifMemoryBlockType.OME
                elif file.endswith('.aivia.tif'):
                    self.type = LifMemoryBlockType.AIVIA
                elif file.endswith('.tif'):
                    self.type = LifMemoryBlockType.TIF
                elif file.endswith('.jpg'):
                    self.type = LifMemoryBlockType.JPG
                elif file.endswith('.png'):
                    self.type = LifMemoryBlockType.PNG
                elif file.endswith('.bmp'):
                    self.type = LifMemoryBlockType.BMP
            return

        if parent.type == LifFileType.LOF:
            fmtstr = '<BQ'
        elif parent.version == 2 or parent.type == LifFileType.LIFEXT:
            fmtstr = '<IIBQBI'
        elif parent.version == 1:
            fmtstr = '<IIBIBI'
        else:
            msg = f'invalid memory block {parent.version=}'
            raise ValueError(msg)

        fh = parent.filehandle
        size = struct.calcsize(fmtstr)
        buffer = fh.read(size)
        if len(buffer) != size:
            raise OSError

        if parent.type == LifFileType.LOF:
            self.id = 'MemBlock_0'  # updated in LifFile._init
            id0, size = struct.unpack(fmtstr, buffer)
            if id0 != 0x2A:
                msg = f'corrupted LOF memory block ({id0=:02X} != 0x2A)'
                raise LifFileError(msg)
        else:
            # parent.type == LifFileType.LIF:
            id0, _, id1, size1, id2, strlen = struct.unpack(fmtstr, buffer)
            if id0 != 0x70 or id1 != 0x2A or id2 != 0x2A:
                msg = (
                    f'corrupted LIF memory block ({id0=:02X} != 0x70, '
                    f'{id1=:02X} != 0x2A, or {id2=:02X} != 0x2A)'
                )
                raise LifFileError(msg)

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

    @overload
    def read(self, /, *, copy: Literal[True] = ...) -> bytes: ...

    @overload
    def read(
        self, /, *, copy: Literal[False]
    ) -> bytes | bytearray | memoryview: ...

    @overload
    def read(self, /, *, copy: bool) -> bytes | bytearray | memoryview: ...

    def read(self, /, *, copy: bool = True) -> bytes | bytearray | memoryview:
        """Return memory block from file.

        Parameters:
            copy:
                Return detached bytes copy.
                If False, return a zero-copy ``memoryview`` for memory-mapped
                files, a ``bytearray`` for external frame blocks, or ``bytes``
                otherwise.

        Returns:
            Memory block data.

        """
        buffer: bytes | bytearray | memoryview

        if len(self.frames) == 1 and self.frames[0].file.endswith('.lof'):
            # allow reading FLIM data from LOF file
            path = os.path.join(self.parent.dirname, self.frames[0].file)
            if not os.path.exists(path):
                path = case_sensitive_path(path)
            with LifFile(path, memmap=self.parent._memmap) as lof:
                return lof.images[0].memory_block.read(copy=copy)

        if len(self.frames) > 0:
            dirname = self.parent.dirname
            buffer = bytearray(self.size)
            for frame in self.frames:
                im = frame.imread(dirname)
                buffer[frame.offset : frame.offset + frame.size] = im.tobytes()
            return bytes(buffer) if copy else buffer

        buffer = self.parent._read_at(self.offset, self.size)
        if len(buffer) != self.size:
            msg = f'read {len(buffer)} bytes, expected {self.size}'
            raise OSError(msg)
        return bytes(buffer) if copy else buffer

    def readinto(self, buffer: NDArray[Any], /) -> None:
        """Read memory block from file into contiguous ndarray."""
        if not buffer.flags.c_contiguous:
            msg = 'buffer must be contiguous'
            raise ValueError(msg)
        if buffer.nbytes != self.size:
            msg = f'{buffer.nbytes} != {self.size=}'
            raise ValueError(msg)
        buffer = buffer.reshape(-1).view(numpy.uint8)

        if self.parent.type == LifFileType.XLIF:
            for frame in self.frames:
                im = frame.imread(self.parent.dirname)
                im = im.reshape(-1).view(numpy.uint8)
                buffer[frame.offset : frame.offset + frame.size] = im
            return

        nbytes = self.parent._read_into(self.offset, buffer)
        if nbytes != self.size:
            msg = f'read {nbytes} bytes, expected {self.size}'
            raise OSError(msg)

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
                of ``shape`` and ``dtype``.
                If a ``file name`` or ``open file``, create a
                memory-mapped array in the specified file.

        """
        dtype = numpy.dtype(dtype)
        nbytes = product(shape) * dtype.itemsize
        if nbytes > self.size:
            msg = f'array size={nbytes} > memory block size={self.size}'
            raise ValueError(msg)
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
            and self.parent.type == LifFileType.XLIF
            and len(self.frames) == 1
        ):
            # avoid copy single frame to output array
            data = self.frames[0].imread(self.parent.dirname)
            # create view in case float16 are stored as uint16 in TIFF
            return data.view(dtype).reshape(shape)

        if out is None and self.offset >= 0:
            return self.parent._read_array(
                self.offset, product(shape), dtype
            ).reshape(shape)

        data = create_output(out, shape, dtype)
        if data.nbytes != nbytes:
            msg = 'size mismatch'
            raise ValueError(msg)

        self.readinto(data)

        if out is not None and hasattr(out, 'flush'):
            out.flush()

        return data

    def __repr__(self) -> str:
        frames = f' frames={len(self.frames)}' if len(self.frames) > 0 else ''
        id_or_type = f'{self.id!r}' if self.id else self.type.name.lower()
        return (
            f'<{self.__class__.__name__} {id_or_type} '
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
            msg = f'unsupported file extension {ext!r}'
            raise ValueError(msg)
        path = os.path.join(dirname, self.file)
        if not os.path.exists(path):
            path = case_sensitive_path(path)
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
                msg = f'frame size={self.size!r} != array size={im.nbytes}'
                raise ValueError(msg)
        return im

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} {self.file!r} '
            f'offset={self.offset} size={self.size} uuid={self.uuid!r}>'
        )


@dataclass(slots=True, frozen=True)
class LifChannel:
    """Attributes of Image/ChannelDescription XML element."""

    dtype: numpy.dtype[Any]
    """Numpy dtype from data_type and resolution."""

    data_type: int
    """Data type, integer (0) or float (1)."""

    channel_tag: int
    """Gray (0), Red (1), Green (2), or Blue (3)."""

    resolution: int
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
    """Distance from first channel in bytes."""

    bit_inc: int
    """Bit distance."""


@dataclass(slots=True, frozen=True)
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
    """Distance from one element to next."""

    bit_inc: int
    """Bit distance."""


@dataclass(slots=True, frozen=True)
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
    """Sequential mode."""


@dataclass(slots=True, frozen=True)
class LifTileScanInfo:
    """Tile scan information from TileScanInfo XML element."""

    flip_x: bool
    """X stage direction is flipped."""

    flip_y: bool
    """Y stage direction is flipped."""

    swap_xy: bool
    """XY dimensions are swapped."""

    tiles: NDArray[numpy.void]
    """Tile indices and positions: field_y, field_x, pos_z, pos_y, pos_x."""

    def __len__(self) -> int:
        """Return number of tiles."""
        return len(self.tiles)

    def __getitem__(self, key: int | str) -> NDArray[Any]:
        """Return field indices and positions."""
        return self.tiles[key]


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
        del kwargs
        msg = (
            f'reading {os.path.splitext(filename)!r} '
            "files requires the 'imagecodecs' package"
        )
        raise ImportError(msg)

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
    6: 'A',  # rotation
    7: 'N',  # XT slices
    8: 'Q',  # T slices. TODO: what does LASX use?
    9: 'Λ',  # excitation wavelength
    10: 'M',  # mosaic position. 'S' in LAS X (StagePos)
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
    '.lif': LifFileType.LIF,
    '.lof': LifFileType.LOF,
    '.xlif': LifFileType.XLIF,
    '.xlef': LifFileType.XLEF,
    '.xlcf': LifFileType.XLCF,
    '.xllf': LifFileType.XLLF,
    '.lifext': LifFileType.LIFEXT,
}
"""Supported file extensions of Leica image files."""


def create_output(
    out: OutputType,
    /,
    shape: Sequence[int],
    dtype: DTypeLike | None,
    *,
    mode: Literal['r+', 'w+', 'r', 'c'] = 'w+',
    suffix: str | None = None,
    fillvalue: float | None = None,
) -> NDArray[Any] | numpy.memmap[Any, Any]:
    """Return NumPy array where data of shape and dtype can be copied.

    Parameters:
        out:
            Specifies kind of array of ``shape`` and ``dtype`` to return:

                ``None``:
                    Return new array.
                ``numpy.ndarray``:
                    Return view of existing array.
                ``'memmap'`` or ``'memmap:tempdir'``:
                    Return memory-map to array stored in temporary binary file.
                ``str`` or open file:
                    Return memory-map to array stored in specified binary file.
        shape:
            Shape of array to return.
        dtype:
            Data type of array to return.
            If ``out`` is an existing array, ``dtype`` must be castable to its
            data type.
        mode:
            File mode to create memory-mapped array.
            The default is ``'w+'`` to create new, or overwrite existing file
            for reading and writing.
        suffix:
            Suffix of ``NamedTemporaryFile`` if ``out`` is ``'memmap'``.
            The default is ``'.memmap'``.
        fillvalue:
            Value to initialize output array.
            By default, return uninitialized array.

    Returns:
        NumPy array or memory-mapped array of ``shape`` and ``dtype``.

    Raises:
        ValueError:
            Existing array cannot be reshaped to ``shape``
            or cast to ``dtype``.

    """
    shape = tuple(shape)
    dtype = numpy.dtype(dtype)
    if out is None:
        if fillvalue is None:
            return numpy.empty(shape, dtype)
        if fillvalue:
            return numpy.full(shape, fillvalue, dtype)
        return numpy.zeros(shape, dtype)
    if isinstance(out, numpy.ndarray):
        if product(shape) != product(out.shape):
            msg = f'cannot reshape {shape} to {out.shape}'
            raise ValueError(msg)
        if not numpy.can_cast(dtype, out.dtype):
            msg = f'cannot cast {dtype} to {out.dtype}'
            raise ValueError(msg)
        if out.shape != shape:
            out = out.reshape(shape, copy=False)
        if fillvalue is not None:
            out.fill(fillvalue)
        return out
    if isinstance(out, str) and out[:6] == 'memmap':
        import tempfile

        tempdir = out[7:] if len(out) > 7 else None
        if suffix is None:
            suffix = '.memmap'
        with tempfile.NamedTemporaryFile(dir=tempdir, suffix=suffix) as fh:
            out = numpy.memmap(fh, shape=shape, dtype=dtype, mode=mode)
            if fillvalue is not None:
                out.fill(fillvalue)
            return out
    out = numpy.memmap(out, shape=shape, dtype=dtype, mode=mode)
    if fillvalue is not None:
        out.fill(fillvalue)
    return out


def product(iterable: Iterable[int], /) -> int:
    """Return product of integers.

    Like math.prod, but does not overflow with numpy arrays.

    """
    prod = 1
    for i in iterable:
        prod *= int(i)
    return prod


@lru_cache(maxsize=128)
def case_sensitive_path(path: str, /) -> str:
    """Return actual case of path on case-sensitive file systems.

    Recursively walk directory tree to find actual case of each path component.
    Results are cached for better performance.

    Parameters:
        path: Path to check.

    Returns:
        Path with correct case.

    Raises:
        FileNotFoundError: Path does not exist or is not accessible.

    """
    try:
        if os.path.exists(path):
            return str(path)
        path = os.path.abspath(path)
        dirname, basename = os.path.split(path)
        if dirname == path:
            return dirname
        dirname = case_sensitive_path(dirname)
        basename = basename.lower()
        with os.scandir(dirname) as it:
            for entry in it:
                if entry.name.lower() == basename:
                    return os.path.join(dirname, entry.name)
        msg = f'file {str(path)!r} not found'
        raise FileNotFoundError(msg)
    except (OSError, PermissionError) as exc:
        msg = f'file {str(path)!r} not accessible'
        raise FileNotFoundError(msg) from exc


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
        xml_element: XML element to convert.
        sanitize: Remove prefix from etree Element.
        prefix: Prefixes for dictionary keys.
        exclude: Ignore element tags.
        sep: Sequence separator.

    Returns:
        dict: Dictionary representation of XML element.

    """
    at, tx = prefix or ('', '')
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
    text = '\n'.join(str(arg) for arg in args)
    return '\n'.join(
        ('  ' + line if line else line) for line in text.splitlines() if line
    )[2:]


def logger() -> logging.Logger:
    """Return logger for liffile module."""
    return logging.getLogger('liffile')


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

    fltr = False
    if len(argv) == 1:
        path = askopenfilename(
            title='Select a Leica image file',
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
        fltr = True
    else:
        files = argv[1:]

    for filename in files:
        if (
            fltr
            and os.path.splitext(filename)[-1].lower() not in FILE_EXTENSIONS
        ):
            continue
        try:
            with LifFile(filename) as lif:
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
                        print(filename, exc)
        except Exception:
            import traceback

            print('Failed to read', filename)
            traceback.print_exc()
            print()
            continue

    return 0


if __name__ == '__main__':
    sys.exit(main())
