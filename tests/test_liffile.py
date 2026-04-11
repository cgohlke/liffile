# test_liffile.py

# Copyright (c) 2023-2026, Christoph Gohlke
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
# * Neither the name of the copyright holders nor the names of any
#   contributors may be used to endorse or promote products derived
#   from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""Unittests for the liffile package.

:Version: 2026.4.11

"""

import datetime
import glob
import io
import itertools
import os
import pathlib
import re
import sys
import sysconfig
import tempfile
from xml.etree import ElementTree

import numpy
import pytest
import xarray
from numpy.testing import assert_allclose, assert_array_equal
from xarray import DataArray

try:
    import fsspec
except ImportError:
    fsspec = None

import liffile
from liffile import (
    FILE_EXTENSIONS,
    LifFile,
    LifFileError,
    LifFileType,
    LifFlimImage,
    LifImage,
    LifImageABC,
    LifImageFrames,
    LifImageSeries,
    LifMemoryBlock,
    LifMemoryBlockType,
    __version__,
    imread,
    xml2dict,
)
from liffile.liffile import BinaryFile, case_sensitive_path

HERE = pathlib.Path(os.path.dirname(__file__))
DATA = HERE / 'data'


@pytest.fixture
def scanmodes_file():
    """Fixture providing path to ScanModesExamples.lif file."""
    filename = DATA / 'ScanModesExamples.lif'
    if not os.path.exists(filename):
        pytest.skip(f'{filename!r} not found')
    return filename


SCANMODES = [
    ('XT-Slices', {'N': 5, 'C': 2, 'T': 10, 'X': 128}, 'uint8'),
    ('XYZ', {'Z': 5, 'C': 2, 'Y': 128, 'X': 128}, 'uint8'),
    ('XZY', {'Y': 5, 'C': 2, 'Z': 128, 'X': 128}, 'uint8'),
    ('XYT', {'T': 7, 'C': 2, 'Y': 128, 'X': 128}, 'uint8'),
    ('XZT', {'T': 7, 'C': 2, 'Z': 128, 'X': 128}, 'uint8'),
    ('XYZT', {'T': 7, 'Z': 5, 'C': 2, 'Y': 128, 'X': 128}, 'uint8'),
    ('XZYT', {'T': 7, 'Y': 5, 'C': 2, 'Z': 128, 'X': 128}, 'uint8'),
    ('XYLambda', {'λ': 9, 'Y': 128, 'X': 128}, 'uint8'),
    ('XZLambda', {'λ': 9, 'Z': 128, 'X': 128}, 'uint8'),
    ('XYLamdaZ', {'Z': 5, 'λ': 9, 'Y': 128, 'X': 128}, 'uint8'),  # typo
    ('XYLambdaT', {'T': 7, 'λ': 9, 'Y': 128, 'X': 128}, 'uint8'),
    ('XZLambdaT', {'T': 7, 'λ': 9, 'Z': 128, 'X': 128}, 'uint8'),
    ('XYZLambdaT', {'T': 7, 'λ': 9, 'Z': 5, 'Y': 128, 'X': 128}, 'uint8'),
    ('XYZLambda', {'T': 1, 'λ': 9, 'Z': 5, 'Y': 128, 'X': 128}, 'uint8'),
    ('XYTZ', {'Z': 5, 'T': 7, 'Y': 128, 'X': 128}, 'uint8'),
    ('XY_12Bit', {'Y': 128, 'X': 128}, 'uint16'),
    ('Job XYExc', {'Λ': 10, 'Y': 128, 'X': 128}, 'uint8'),
    ('Job XYExcT', {'T': 7, 'Λ': 10, 'Y': 128, 'X': 128}, 'uint8'),
    ('Job XYZExc', {'Λ': 10, 'Z': 5, 'Y': 128, 'X': 128}, 'uint8'),
    ('Job XZEXc', {'Λ': 10, 'Z': 128, 'X': 128}, 'uint8'),
    ('Job XZEXcLambda/Lambda_496nm', {'Λ': 1, 'Z': 128, 'X': 128}, 'uint8'),
    ('Job XZEXcLambda/Lambda_530nm', {'Λ': 2, 'Z': 128, 'X': 128}, 'uint8'),
    ('Job XZEXcLambda/Lambda_564nm', {'Λ': 4, 'Z': 128, 'X': 128}, 'uint8'),
    ('Job XZEXcLambda/Lambda_598nm', {'Λ': 5, 'Z': 128, 'X': 128}, 'uint8'),
    ('Job XZEXcLambda/Lambda_632nm', {'Λ': 7, 'Z': 128, 'X': 128}, 'uint8'),
    ('Job XZEXcLambda/Lambda_666nm', {'Λ': 8, 'Z': 128, 'X': 128}, 'uint8'),
    ('Job XZEXcLambda/Lambda_700nm', {'Λ': 10, 'Z': 128, 'X': 128}, 'uint8'),
    ('Job XZEXcLambda/Lambda_734nm', {'Λ': 10, 'Z': 128, 'X': 128}, 'uint8'),
    ('Job XZEXcLambda/Lambda_769nm', {'Λ': 10, 'Z': 128, 'X': 128}, 'uint8'),
    ('Job XYExcLambda /Lambda_496nm', {'Λ': 1, 'Y': 128, 'X': 128}, 'uint8'),
    ('Job XYExcLambda /Lambda_530nm', {'Λ': 2, 'Y': 128, 'X': 128}, 'uint8'),
    ('Job XYExcLambda /Lambda_564nm', {'Λ': 4, 'Y': 128, 'X': 128}, 'uint8'),
    ('Job XYExcLambda /Lambda_598nm', {'Λ': 5, 'Y': 128, 'X': 128}, 'uint8'),
    ('Job XYExcLambda /Lambda_632nm', {'Λ': 7, 'Y': 128, 'X': 128}, 'uint8'),
    ('Job XYExcLambda /Lambda_666nm', {'Λ': 8, 'Y': 128, 'X': 128}, 'uint8'),
    ('Job XYExcLambda /Lambda_700nm', {'Λ': 10, 'Y': 128, 'X': 128}, 'uint8'),
    ('Job XYExcLambda /Lambda_734nm', {'Λ': 10, 'Y': 128, 'X': 128}, 'uint8'),
    ('Job XYExcLambda /Lambda_769nm', {'Λ': 10, 'Y': 128, 'X': 128}, 'uint8'),
    (
        'Mark_and_Find_XYExc/Position1001',
        {'Λ': 10, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYExc/Position2002',
        {'Λ': 10, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYExc/Position3003',
        {'Λ': 10, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYExcT/Position1001',
        {'T': 7, 'Λ': 10, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYExcT/Position2002',
        {'T': 7, 'Λ': 10, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYExcT/Position3003',
        {'T': 7, 'Λ': 10, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYZExc/Position1001',
        {'Λ': 10, 'Z': 5, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYZExc/Position2002',
        {'Λ': 10, 'Z': 5, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYZExc/Position3003',
        {'Λ': 10, 'Z': 5, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XZExc/Position1001',
        {'Λ': 10, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XZExc/Position2002',
        {'Λ': 10, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XZExc/Position3003',
        {'Λ': 10, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XZYT/Position1001',
        {'T': 7, 'Y': 5, 'C': 2, 'Z': 256, 'X': 256},
        'uint8',
    ),
    (
        'Mark_and_Find_XZYT/Position2002',
        {'T': 7, 'Y': 5, 'C': 2, 'Z': 256, 'X': 256},
        'uint8',
    ),
    (
        'Mark_and_Find_XZYT/Position3003',
        {'T': 7, 'Y': 5, 'C': 2, 'Z': 256, 'X': 256},
        'uint8',
    ),
    (
        'Mark_and_Find_XZY/Position1001',
        {'Y': 5, 'C': 2, 'Z': 32, 'X': 512},
        'uint8',
    ),
    (
        'Mark_and_Find_XZY/Position2002',
        {'Y': 5, 'C': 2, 'Z': 32, 'X': 512},
        'uint8',
    ),
    (
        'Mark_and_Find_XZY/Position3003',
        {'Y': 5, 'C': 2, 'Z': 32, 'X': 512},
        'uint8',
    ),
    (
        'Mark_and_Find_XYZ/Position1001',
        {'Z': 5, 'C': 4, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYZ/Position2002',
        {'Z': 5, 'C': 4, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYZ/Position3003',
        {'Z': 5, 'C': 4, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYZ/Position4004',
        {'Z': 5, 'C': 4, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYZ/Position5005',
        {'Z': 5, 'C': 4, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYZ/Position6006',
        {'Z': 5, 'C': 4, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYT/Position1001',
        {'T': 7, 'C': 4, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYT/Position2002',
        {'T': 7, 'C': 4, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYT/Position3003',
        {'T': 7, 'C': 4, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYT/Position4004',
        {'T': 7, 'C': 4, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYT/Position5005',
        {'T': 7, 'C': 4, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYT/Position6006',
        {'T': 7, 'C': 4, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYZT/Position1001',
        {'T': 7, 'Z': 5, 'C': 4, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYZT/Position2002',
        {'T': 7, 'Z': 5, 'C': 4, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYZT/Position3003',
        {'T': 7, 'Z': 5, 'C': 4, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYZT/Position4004',
        {'T': 7, 'Z': 5, 'C': 4, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYZT/Position5005',
        {'T': 7, 'Z': 5, 'C': 4, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYZT/Position6006',
        {'T': 7, 'Z': 5, 'C': 4, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYLambda/Position1001',
        {'λ': 9, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYLambda/Position2002',
        {'λ': 9, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYLambda/Position3003',
        {'λ': 9, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYLambda/Position4004',
        {'λ': 9, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYLambda/Position5005',
        {'λ': 9, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYLambda/Position6006',
        {'λ': 9, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYLambdaZ/Position1001',
        {'Z': 5, 'λ': 9, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYLambdaZ/Position2002',
        {'Z': 5, 'λ': 9, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYLambdaZ/Position3003',
        {'Z': 5, 'λ': 9, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYLambdaZ/Position4004',
        {'Z': 5, 'λ': 9, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYLambdaZ/Position5005',
        {'Z': 5, 'λ': 9, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYLambdaZ/Position6006',
        {'Z': 5, 'λ': 9, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYLambdaT/Position1001',
        {'T': 7, 'λ': 9, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYLambdaT/Position2002',
        {'T': 7, 'λ': 9, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYLambdaT/Position3003',
        {'T': 7, 'λ': 9, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYLambdaT/Position4004',
        {'T': 7, 'λ': 9, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYLambdaT/Position5005',
        {'T': 7, 'λ': 9, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYLambdaT/Position6006',
        {'T': 7, 'λ': 9, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYZLambdaT/Position1001',
        {'T': 7, 'λ': 9, 'Z': 5, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYZLambdaT/Position2002',
        {'T': 7, 'λ': 9, 'Z': 5, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYZLambdaT/Position3003',
        {'T': 7, 'λ': 9, 'Z': 5, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYZLambdaT/Position4004',
        {'T': 7, 'λ': 9, 'Z': 5, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYZLambdaT/Position5005',
        {'T': 7, 'λ': 9, 'Z': 5, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XYZLambdaT/Position6006',
        {'T': 7, 'λ': 9, 'Z': 5, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XZLambda/Position2002',
        {'λ': 9, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XZLambda/Position3003',
        {'λ': 9, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XZLambda/Position4004',
        {'λ': 9, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XZLambda/Position5005',
        {'λ': 9, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XZLambda/Position6006',
        {'λ': 9, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XZLambda/Position7007',
        {'λ': 9, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XZLambdaT/Position2002',
        {'T': 7, 'λ': 9, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XZLambdaT/Position3003',
        {'T': 7, 'λ': 9, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XZLambdaT/Position4004',
        {'T': 7, 'λ': 9, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XZLambdaT/Position5005',
        {'T': 7, 'λ': 9, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XZLambdaT/Position6006',
        {'T': 7, 'λ': 9, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'Mark_and_Find_XZLambdaT/Position7007',
        {'T': 7, 'λ': 9, 'Z': 128, 'X': 128},
        'uint8',
    ),
    ('Mark_and_Find_XT/Position2002', {'N': 4, 'T': 128, 'X': 128}, 'uint8'),
    ('Mark_and_Find_XT/Position3003', {'N': 4, 'T': 128, 'X': 128}, 'uint8'),
    ('Mark_and_Find_XT/Position4004', {'N': 4, 'T': 128, 'X': 128}, 'uint8'),
    ('Mark_and_Find_XT/Position5005', {'N': 4, 'T': 128, 'X': 128}, 'uint8'),
    ('Mark_and_Find_XT/Position6006', {'N': 4, 'T': 128, 'X': 128}, 'uint8'),
    ('Mark_and_Find_XT/Position7007', {'N': 4, 'T': 128, 'X': 128}, 'uint8'),
    (
        'SequenceLambda/Job_XYL095',
        {'L': 3, 'λ': 9, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceLambda/Job_XZL096',
        {'L': 3, 'λ': 9, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (  # T and L have same bytes_inc but T is before L in XML
        'SequenceLambda/Job_XYZL097',
        {'T': 1, 'L': 3, 'λ': 9, 'Z': 5, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceLambda/Job_XYLZ098',
        {'L': 3, 'Z': 5, 'λ': 9, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceLambda/Job_XYLT099',
        {'L': 3, 'T': 7, 'λ': 9, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceLambda/Job_XZLT100',
        {'L': 3, 'T': 7, 'λ': 9, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceLambda/Job_XYZLT101',
        {'L': 3, 'T': 7, 'λ': 9, 'Z': 5, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceOrtZeit/Job_XT001',
        {'N': 1, 'L': 3, 'T': 512, 'X': 128},
        'uint8',
    ),
    (
        'SequenceOrtZeit/Job_XYZ1_002',
        {'Z': 1, 'L': 3, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceOrtZeit/Job_XYT003',
        {'L': 3, 'T': 7, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceOrtZeit/Job_XYTZ004',
        {'L': 3, 'Z': 5, 'T': 7, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceOrtZeit/Job_XYZ005',
        {'L': 3, 'Z': 5, 'C': 4, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceOrtZeit/Job_XYZT006',
        {'L': 3, 'T': 7, 'Z': 5, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceOrtZeit/Job_XZT007',
        {'L': 3, 'T': 7, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceOrtZeit/Job_XZY008',
        {'L': 3, 'Y': 5, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceOrtZeit/Job_XZYT009',
        {'L': 3, 'T': 7, 'Z': 5, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/Job XYEXc 01_020',
        {'L': 3, 'Λ': 10, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/Job XYEXcT 01_021',
        {'L': 3, 'T': 7, 'Λ': 10, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/Job XYZEXc 01_022',
        {'L': 3, 'Λ': 10, 'Z': 5, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/Job XZEXc 01_023',
        {'L': 3, 'Λ': 10, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/LambdaLambda_004/Lambda_496nm',
        {'Λ': 1, 'L': 3, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/LambdaLambda_004/Lambda_530nm',
        {'L': 3, 'Λ': 2, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/LambdaLambda_004/Lambda_564nm',
        {'L': 3, 'Λ': 4, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/LambdaLambda_004/Lambda_598nm',
        {'L': 3, 'Λ': 5, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/LambdaLambda_004/Lambda_632nm',
        {'L': 3, 'Λ': 7, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/LambdaLambda_004/Lambda_666nm',
        {'L': 3, 'Λ': 8, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/LambdaLambda_004/Lambda_700nm',
        {'L': 3, 'Λ': 10, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/LambdaLambda_004/Lambda_734nm',
        {'L': 3, 'Λ': 10, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/LambdaLambda_004/Lambda_769nm',
        {'L': 3, 'Λ': 10, 'Z': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/LambdaLambda_005/Lambda_496nm',
        {'Λ': 1, 'L': 3, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/LambdaLambda_005/Lambda_530nm',
        {'L': 3, 'Λ': 2, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/LambdaLambda_005/Lambda_564nm',
        {'L': 3, 'Λ': 4, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/LambdaLambda_005/Lambda_598nm',
        {'L': 3, 'Λ': 5, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/LambdaLambda_005/Lambda_632nm',
        {'L': 3, 'Λ': 7, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/LambdaLambda_005/Lambda_666nm',
        {'L': 3, 'Λ': 8, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/LambdaLambda_005/Lambda_700nm',
        {'L': 3, 'Λ': 10, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/LambdaLambda_005/Lambda_734nm',
        {'L': 3, 'Λ': 10, 'Y': 128, 'X': 128},
        'uint8',
    ),
    (
        'SequenceExc/LambdaLambda_005/Lambda_769nm',
        {'L': 3, 'Λ': 10, 'Y': 128, 'X': 128},
        'uint8',
    ),
    ('Mark_and_Find_XZT/Position2002', {'T': 7, 'Z': 128, 'X': 128}, 'uint8'),
    ('Mark_and_Find_XZT/Position3003', {'T': 7, 'Z': 128, 'X': 128}, 'uint8'),
    ('Mark_and_Find_XZT/Position4004', {'T': 7, 'Z': 128, 'X': 128}, 'uint8'),
    ('Mark_and_Find_XZT/Position5005', {'T': 7, 'Z': 128, 'X': 128}, 'uint8'),
    ('Mark_and_Find_XZT/Position6006', {'T': 7, 'Z': 128, 'X': 128}, 'uint8'),
    ('Mark_and_Find_XZT/Position7007', {'T': 7, 'Z': 128, 'X': 128}, 'uint8'),
    ('Widefield.lif/XY_8Bit', {'Y': 130, 'X': 172}, 'uint8'),
    ('Widefield.lif/XYZ_8Bit', {'Z': 5, 'Y': 130, 'X': 172}, 'uint8'),
    ('Widefield.lif/XYT_8Bit', {'T': 7, 'Y': 130, 'X': 172}, 'uint8'),
    ('Widefield.lif/XYZT_8Bit', {'T': 7, 'Z': 5, 'Y': 130, 'X': 172}, 'uint8'),
    ('Widefield.lif/XY_12Bit', {'Y': 130, 'X': 172}, 'uint16'),
    ('Widefield.lif/XYZ_12Bit', {'Z': 5, 'Y': 130, 'X': 172}, 'uint16'),
    ('Widefield.lif/XYT_12Bit', {'T': 7, 'Y': 130, 'X': 172}, 'uint16'),
    (
        'Widefield.lif/XYZT_12Bit',
        {'T': 7, 'Z': 5, 'Y': 130, 'X': 172},
        'uint16',
    ),
    (
        'Widefield.lif/Mark_and_Find_XY_12Bit/Position1001',
        {'Y': 130, 'X': 172},
        'uint16',
    ),
    (
        'Widefield.lif/Mark_and_Find_XY_12Bit/Position2002',
        {'Y': 130, 'X': 172},
        'uint16',
    ),
    (
        'Widefield.lif/Mark_and_Find_XY_12Bit/Position3003',
        {'Y': 130, 'X': 172},
        'uint16',
    ),
    (
        'Widefield.lif/Mark_and_Find_XY_8Bit/Position1001',
        {'Y': 130, 'X': 172},
        'uint8',
    ),
    (
        'Widefield.lif/Mark_and_Find_XY_8Bit/Position2002',
        {'Y': 130, 'X': 172},
        'uint8',
    ),
    (
        'Widefield.lif/Mark_and_Find_XY_8Bit/Position3003',
        {'Y': 130, 'X': 172},
        'uint8',
    ),
    (
        'Widefield.lif/Mark_and_Find_XYZ_8Bit/Position1001',
        {'Z': 5, 'Y': 130, 'X': 172},
        'uint8',
    ),
    (
        'Widefield.lif/Mark_and_Find_XYZ_8Bit/Position2002',
        {'Z': 5, 'Y': 130, 'X': 172},
        'uint8',
    ),
    (
        'Widefield.lif/Mark_and_Find_XYZ_8Bit/Position3003',
        {'Z': 5, 'Y': 130, 'X': 172},
        'uint8',
    ),
    (
        'Widefield.lif/Mark_and_Find_XYZ_12Bit/Position1001',
        {'Z': 5, 'Y': 130, 'X': 172},
        'uint16',
    ),
    (
        'Widefield.lif/Mark_and_Find_XYZ_12Bit/Position2002',
        {'Z': 5, 'Y': 130, 'X': 172},
        'uint16',
    ),
    (
        'Widefield.lif/Mark_and_Find_XYZ_12Bit/Position3003',
        {'Z': 5, 'Y': 130, 'X': 172},
        'uint16',
    ),
    (
        'Widefield.lif/Mark_and_Find_XYZT_12Bit/Position1001',
        {'T': 7, 'Z': 5, 'Y': 130, 'X': 172},
        'uint16',
    ),
    (
        'Widefield.lif/Mark_and_Find_XYZT_12Bit/Position2002',
        {'T': 7, 'Z': 5, 'Y': 130, 'X': 172},
        'uint16',
    ),
    (
        'Widefield.lif/Mark_and_Find_XYZT_12Bit/Position3003',
        {'T': 7, 'Z': 5, 'Y': 130, 'X': 172},
        'uint16',
    ),
    (
        'Widefield.lif/Mark_and_Find_XYZT_8Bit/Position1001',
        {'T': 7, 'Z': 5, 'Y': 130, 'X': 172},
        'uint8',
    ),
    (
        'Widefield.lif/Mark_and_Find_XYZT_8Bit/Position2002',
        {'T': 7, 'Z': 5, 'Y': 130, 'X': 172},
        'uint8',
    ),
    (
        'Widefield.lif/Mark_and_Find_XYZT_8Bit/Position3003',
        {'T': 7, 'Z': 5, 'Y': 130, 'X': 172},
        'uint8',
    ),
    (
        'Widefield.lif/Mark_and_Find_XYT_8Bit/Position1001',
        {'T': 7, 'Y': 130, 'X': 172},
        'uint8',
    ),
    (
        'Widefield.lif/Mark_and_Find_XYT_8Bit/Position2002',
        {'T': 7, 'Y': 130, 'X': 172},
        'uint8',
    ),
    (
        'Widefield.lif/Mark_and_Find_XYT_8Bit/Position3003',
        {'T': 7, 'Y': 130, 'X': 172},
        'uint8',
    ),
    (
        'Widefield.lif/Mark_and_Find_XYT_12Bit/Position1001',
        {'T': 7, 'Y': 130, 'X': 172},
        'uint16',
    ),
    (
        'Widefield.lif/Mark_and_Find_XYT_12Bit/Position2002',
        {'T': 7, 'Y': 130, 'X': 172},
        'uint16',
    ),
    (
        'Widefield.lif/Mark_and_Find_XYT_12Bit/Position3003',
        {'T': 7, 'Y': 130, 'X': 172},
        'uint16',
    ),
    (
        'Widefield.lif/Sequence_8Bit_2Loops/XY042',
        {'L': 2, 'Y': 130, 'X': 172},
        'uint8',
    ),
    (
        'Widefield.lif/Sequence_8Bit_2Loops/XYZ043',
        {'L': 2, 'Z': 9, 'Y': 130, 'X': 172},
        'uint8',
    ),
    (
        'Widefield.lif/Sequence_8Bit_2Loops/XYT044',
        {'L': 2, 'T': 7, 'Y': 130, 'X': 172},
        'uint8',
    ),
    (
        'Widefield.lif/Sequence_8Bit_2Loops/XYZT045',
        {'L': 2, 'T': 7, 'Z': 5, 'Y': 130, 'X': 172},
        'uint8',
    ),
    (
        'Widefield.lif/Sequence_12Bit_3Loops/XY054',
        {'L': 3, 'Y': 130, 'X': 172},
        'uint16',
    ),
    (
        'Widefield.lif/Sequence_12Bit_3Loops/XYZ055',
        {'L': 3, 'Z': 9, 'Y': 130, 'X': 172},
        'uint16',
    ),
    (
        'Widefield.lif/Sequence_12Bit_3Loops/XYT056',
        {'L': 3, 'T': 7, 'Y': 130, 'X': 172},
        'uint16',
    ),
    (
        'Widefield.lif/Sequence_12Bit_3Loops/XYZT057',
        {'L': 3, 'T': 7, 'Z': 5, 'Y': 130, 'X': 172},
        'uint16',
    ),
]


def _assert_frames(image: LifImage, expected: numpy.ndarray) -> None:
    """Assert frame access methods are consistent with asarray data."""
    frames = image.frames
    assert isinstance(frames, LifImageFrames)
    repr(frames)
    str(frames)

    # assert frame_sizes are consistent
    frame_sizes = frames.frame_sizes
    assert isinstance(frame_sizes, dict)
    assert tuple(frame_sizes.keys()) == frames.frame_dims
    assert tuple(frame_sizes.values()) == frames.frame_shape

    # frame dimensions must be suffix of image dimensions
    if frame_sizes:
        frame_dims = tuple(frame_sizes.keys())
        frame_shape = tuple(frame_sizes.values())
        assert image.dims[-len(frame_sizes) :] == frame_dims
        assert image.shape[-len(frame_sizes) :] == frame_shape
    else:
        # no contiguous frame dimensions identified, cannot iterate frames
        return

    # assert iteration dimensions
    non_frame_dims = [d for d in image.dims if d not in frame_sizes]
    if not non_frame_dims:
        # single frame image should yield one empty tuple
        assert list(frames.keys()) == [()]
        return

    # count total frames
    expected_count = 1
    for dim in non_frame_dims:
        expected_count *= image.sizes[dim]
    assert len(frames) == expected_count
    assert len(tuple(frames.keys())) == expected_count

    # test selection with int (fixed index)
    first_dim = non_frame_dims[0]
    fixed_frames = frames(**{first_dim: 0})
    expected_fixed = expected_count // image.sizes[first_dim]
    assert len(fixed_frames) == expected_fixed

    # test selection with slice
    if image.sizes[non_frame_dims[0]] > 2:
        dim = non_frame_dims[0]
        sliced_frames = frames(**{dim: slice(0, 2)})
        expected_sliced = expected_count // image.sizes[dim] * 2
        assert len(sliced_frames) == expected_sliced

    # test selection with sequence
    if image.sizes[non_frame_dims[0]] > 1:
        dim = non_frame_dims[0]
        seq_frames = frames(**{dim: [0]})
        expected_seq = expected_count // image.sizes[dim]
        assert len(seq_frames) == expected_seq

    # first frame should match
    assert_array_equal(image.frame(), frames[0])

    for frame in frames.values():
        assert_array_equal(frame, frames[0])
        break

    # frames.asarray should match image.asarray()
    out = numpy.empty(frames.shape, frames.dtype)
    xout = frames.asxarray(out=out)
    assert_array_equal(out, expected)
    assert isinstance(xout, xarray.DataArray)


@pytest.mark.skipif(__doc__ is None, reason='__doc__ is None')
def test_version():
    """Assert liffile versions match docstrings."""
    ver = ':Version: ' + __version__
    assert ver in __doc__
    assert ver in liffile.__doc__


class TestBinaryFile:
    """Test BinaryFile with different file-like inputs."""

    def setup_method(self):
        self.filename = os.path.normpath(DATA / 'binary.bin')
        if not os.path.exists(self.filename):
            pytest.skip(f'{self.filename!r} not found')

    def validate(
        self,
        fh: BinaryFile,
        filepath: str | None = None,
        filename: str | None = None,
        dirname: str | None = None,
        name: str | None = None,
        *,
        closed: bool = True,
    ) -> None:
        """Assert BinaryFile attributes."""
        if filepath is None:
            filepath = self.filename
        if filename is None:
            filename = os.path.basename(self.filename)
        if dirname is None:
            dirname = os.path.dirname(self.filename)
        if name is None:
            name = fh.filename

        attrs = fh.attrs
        assert attrs['name'] == name
        assert attrs['filepath'] == filepath

        assert fh.filepath == filepath
        assert fh.filename == filename
        assert fh.dirname == dirname
        assert fh.name == name
        assert fh.closed is False
        assert len(fh.filehandle.read()) == 256
        fh.filehandle.seek(10)
        assert fh.filehandle.tell() == 10
        assert fh.filehandle.read(1) == b'\n'
        fh.close()
        # underlying filehandle may still be be open if
        # BinaryFile was given an open filehandle
        assert fh._fh.closed is closed
        # BinaryFile always reports itself as closed after close() is called
        assert fh.closed

    def test_str(self):
        """Test BinaryFile with str path."""
        file = self.filename
        with BinaryFile(file) as fh:
            self.validate(fh, closed=True)

    def test_pathlib(self):
        """Test BinaryFile with pathlib.Path."""
        file = pathlib.Path(self.filename)
        with BinaryFile(file) as fh:
            self.validate(fh, closed=True)

    def test_open_file(self):
        """Test BinaryFile with open binary file."""
        with open(self.filename, 'rb') as fh, BinaryFile(fh) as bf:
            self.validate(bf, closed=False)

    def test_bytesio(self):
        """Test BinaryFile with BytesIO."""
        with open(self.filename, 'rb') as fh:
            file = io.BytesIO(fh.read())
        with BinaryFile(file) as fh:
            self.validate(
                fh,
                filepath='',
                filename='',
                dirname='',
                name='BytesIO',
                closed=False,
            )

    @pytest.mark.skipif(fsspec is None, reason='fsspec not installed')
    def test_fsspec_openfile(self):
        """Test BinaryFile with fsspec OpenFile."""
        file = fsspec.open(self.filename)
        with BinaryFile(file) as fh:
            self.validate(fh, closed=True)

    @pytest.mark.skipif(fsspec is None, reason='fsspec not installed')
    def test_fsspec_localfileopener(self):
        """Test BinaryFile with fsspec LocalFileOpener."""
        with fsspec.open(self.filename) as file, BinaryFile(file) as fh:
            self.validate(fh, closed=False)

    def test_text_file_fails(self):
        """Test BinaryFile with open text file fails."""
        with open(self.filename) as fh:  # noqa: SIM117
            with pytest.raises(TypeError):
                BinaryFile(fh)

    def test_file_extension_fails(self):
        """Test BinaryFile with wrong file extension fails."""
        ext = BinaryFile._ext
        BinaryFile._ext = {'.lif'}
        try:
            with pytest.raises(ValueError):
                BinaryFile(self.filename)
        finally:
            BinaryFile._ext = ext

    def test_file_not_seekable(self):
        """Test BinaryFile with non-seekable file fails."""

        class File:
            # mock file object without tell methods
            def seek(self):
                pass

        with pytest.raises(ValueError):
            BinaryFile(File)

    def test_openfile_not_seekable(self):
        """Test BinaryFile with non-seekable file fails."""

        class File:
            # mock fsspec OpenFile without seek/tell methods
            @staticmethod
            def open(*args, **kwargs):
                del args, kwargs
                return File()

        with pytest.raises(ValueError):
            BinaryFile(File)

    def test_invalid_object(self):
        """Test BinaryFile with invalid file object fails."""

        class File:
            # mock non-file object
            pass

        with pytest.raises(TypeError):
            BinaryFile(File)

    def test_invalid_mode(self):
        """Test BinaryFile with invalid mode fails."""
        with pytest.raises(ValueError):
            BinaryFile(self.filename, mode='ab')


class TestLifFile:
    """Test LifFile with different file-like inputs."""

    @pytest.fixture(autouse=True)
    def setup(self, scanmodes_file):
        """Set up test with scanmodes file."""
        self.filename = os.path.normpath(scanmodes_file)

    def validate(self, lif: LifFile) -> None:
        # assert LifFile attributes
        assert lif.parent is None
        assert not lif.filehandle.closed
        assert lif.name == 'ScanModiBeispiele.lif'
        assert lif.version == 2
        assert lif.datetime == datetime.datetime(
            2013, 12, 2, 8, 27, 44, tzinfo=datetime.UTC
        )
        assert len(lif.memory_blocks) == 240
        assert repr(lif).startswith('<LifFile ')
        assert lif.xml_header().startswith(
            '<LMSDataContainerHeader Version="2">'
        )

        series = lif.images
        str(series)
        assert len(series) == 200
        im = series[5]
        str(im)
        assert series[im.path] is im

    def test_str(self):
        """Test LifFile with str path."""
        file = self.filename
        with LifFile(file) as lif:
            self.validate(lif)

    def test_pathlib(self):
        """Test LifFile with pathlib.Path."""
        file = pathlib.Path(self.filename)
        with LifFile(file) as lif:
            self.validate(lif)

    def test_open_file(self):
        """Test LifFile with open binary file."""
        with open(self.filename, 'rb') as fh, LifFile(fh) as lif:
            self.validate(lif)

    def test_bytesio(self):
        """Test LifFile with BytesIO."""
        with open(self.filename, 'rb') as fh:
            file = io.BytesIO(fh.read())
        with LifFile(file) as lif:
            self.validate(lif)

    @pytest.mark.skipif(fsspec is None, reason='fsspec not installed')
    def test_fsspec_openfile(self):
        """Test LifFile with fsspec OpenFile."""
        file = fsspec.open(self.filename)
        with LifFile(file) as lif:
            self.validate(lif)
        file.close()

    @pytest.mark.skipif(fsspec is None, reason='fsspec not installed')
    def test_fsspec_localfileopener(self):
        """Test LifFile with fsspec LocalFileOpener."""
        with fsspec.open(self.filename) as file, LifFile(file) as lif:
            self.validate(lif)


def test_not_lif():
    """Test open non-LIF file raises exceptions."""
    with pytest.raises(LifFileError):
        imread(DATA / 'empty.bin')
    with pytest.raises(LifFileError):
        imread(DATA / 'ScanModesExamples.lif.xml')
    with pytest.raises(TypeError):
        imread(TypeError)


@pytest.mark.parametrize(
    ('asxarray', 'selection', 'squeeze', 'expected_sizes', 'expected_sum'),
    [
        (
            False,
            None,
            True,
            {'T': 7, 'Z': 5, 'C': 2, 'Y': 128, 'X': 128},
            27141756,
        ),
        (
            True,
            None,
            True,
            {'T': 7, 'Z': 5, 'C': 2, 'Y': 128, 'X': 128},
            27141756,
        ),
        (
            False,
            {'Z': [1, 2], 'T': slice(1, 6), 'C': 1},
            True,
            {'Z': 2, 'T': 5, 'Y': 128, 'X': 128},
            6374235,
        ),
        (
            True,
            {'Z': [1, 2], 'T': slice(1, 6), 'C': 1},
            True,
            {'Z': 2, 'T': 5, 'Y': 128, 'X': 128},
            6374235,
        ),
        (
            False,
            {'Z': [1, 2], 'T': slice(1, 6), 'C': 1},
            False,
            {'Z': 2, 'T': 5, 'C': 1, 'Y': 128, 'X': 128},
            6374235,
        ),
        (
            True,
            {'Z': [1, 2], 'T': slice(1, 6), 'C': 1},
            False,
            {'Z': 2, 'T': 5, 'C': 1, 'Y': 128, 'X': 128},
            6374235,
        ),
    ],
)
def test_imread(
    asxarray, selection, squeeze, expected_sizes, expected_sum, scanmodes_file
):
    """Test imread function with various parameters."""
    data = imread(
        scanmodes_file,
        image=5,
        selection=selection,
        squeeze=squeeze,
        out=None,
        asxarray=asxarray,
    )
    if asxarray:
        assert isinstance(data, DataArray)
        assert data.sizes == expected_sizes
        data = data.data
    else:
        assert isinstance(data, numpy.ndarray)
    assert data.shape == tuple(expected_sizes.values())
    assert data.sum(dtype=numpy.uint32) == expected_sum


@pytest.mark.parametrize('filetype', [str, io.BytesIO])
def test_lif(filetype, scanmodes_file):
    """Test LIF file."""
    file = (
        scanmodes_file
        if filetype is str
        else open(scanmodes_file, 'rb')  # noqa: SIM115
    )

    with LifFile(file, mode='r+b', squeeze=True) as lif:
        str(lif)
        assert lif.parent is None
        if filetype is str:
            assert lif.filename == str(scanmodes_file.name)
            assert lif.dirname == str(scanmodes_file.parent)
        assert not lif.filehandle.closed
        assert lif.name == 'ScanModiBeispiele.lif'
        assert lif.version == 2
        assert lif.uuid == '9da018ae-5b2b-11e3-8f53-eccd6d2154b5'
        assert lif.datetime == datetime.datetime(
            2013, 12, 2, 8, 27, 44, tzinfo=datetime.UTC
        )
        assert len(lif.memory_blocks) == 240
        assert isinstance(lif.xml_element, ElementTree.Element)
        assert repr(lif).startswith('<LifFile ')
        assert lif.xml_header().startswith(
            '<LMSDataContainerHeader Version="2">'
        )

        series = lif.images
        str(series)
        assert isinstance(series, LifImageSeries)
        assert len(series) == 200
        with pytest.raises(IndexError):
            lif.images[200]
        with pytest.raises(KeyError):
            lif.images['ABC']

        for image in series:
            str(image)
            assert isinstance(image, LifImageABC)
            assert isinstance(image, LifImage)

        images = series.findall('XZEXcLambda/Lambda.*', flags=re.IGNORECASE)
        assert len(images) == 9
        assert images[0].name == 'Lambda_496nm'
        assert images[0].parent_image is None
        assert series.findall(images[1].uuid, attr='uuid')[0] is images[1]

        im = series.find('Lambda_496nm', flags=re.IGNORECASE)
        assert im is images[0]
        assert series.find('ABC', default=im) is im
        assert series.find(im.uuid, attr='uuid') is im

        im = series[5]
        str(im)
        assert series[im.path] is im
        assert series[im.name + '$'] is im
        assert im.parent is lif
        assert im.parent_image is None
        assert im.child_images == ()
        assert im.name == 'XYZT'
        assert im.path == 'XYZT'
        assert im.uuid == '06f46831-5b37-11e3-8f53-eccd6d2154b5'
        assert len(im.xml_element) > 0
        assert im.dtype == numpy.uint8
        assert im.itemsize == 1
        assert im.shape == (7, 5, 2, 128, 128)
        assert im.dims == ('T', 'Z', 'C', 'Y', 'X')
        assert im.sizes == {'T': 7, 'Z': 5, 'C': 2, 'Y': 128, 'X': 128}
        assert_array_equal(im.coords['C'], ['Ch0', 'Ch1'])
        assert_allclose(im.coords['T'][[0, -1]], [0.0, 10.657])
        assert_allclose(im.coords['Z'][[0, -1]], [4.999881e-06, -5.000359e-06])
        assert_allclose(im.coords['Y'][[0, -1]], [-3.418137e-05, 3.658182e-04])
        assert_allclose(im.coords['X'][[0, -1]], [8.673617e-20, 3.999996e-04])
        assert im.attrs['path'] == im.parent.name + '/' + im.path
        assert im.timestamps is not None
        assert len(im.timestamps) == 70
        assert im.timestamps[0] == numpy.datetime64('2013-12-02T09:49:26.347')
        assert im.size == 1146880
        assert im.nbytes == 1146880
        assert im.ndim == 5
        assert isinstance(im.xml_element, ElementTree.Element)

        attrs = im.attrs
        assert attrs['filepath'] == im.parent.filepath
        assert attrs['name'] == im.name

        attrs = im.attrs['HardwareSetting']
        assert attrs['Software'] == 'LAS-AF [ BETA ] 3.3.0.10067'
        assert attrs['ATLConfocalSettingDefinition']['LineTime'] == 0.0025

        data = im.asarray(mode='r', out='memmap')
        assert isinstance(data, numpy.memmap), type(data)
        assert data.sum(dtype=numpy.uint64) == 27141756

        xdata = im.asxarray(mode='r', out=None)
        assert isinstance(xdata, xarray.DataArray)
        assert_array_equal(xdata.data, data)
        assert xdata.name == im.name
        assert xdata.dtype == im.dtype
        assert xdata.dims == im.dims
        assert xdata.shape == im.shape
        assert xdata.attrs == im.attrs
        assert_array_equal(xdata.coords['T'], im.coords['T'])

        memory_block = im.memory_block
        str(im.memory_block)
        assert isinstance(memory_block, LifMemoryBlock)
        assert memory_block.id == 'MemBlock_29'
        assert memory_block.offset == 6639225
        assert memory_block.size == 1146880
        assert memory_block.type == LifMemoryBlockType.MEM
        assert memory_block.read() == data.tobytes()

        _assert_frames(im, xdata.data)

        if filetype is str:
            lif.close()
            assert lif.filehandle.closed

    if filetype is not str:
        file.close()
    else:
        with pytest.raises(ValueError):
            lif = LifFile(file, mode='abc')


def test_lof():
    """Test LOF file."""
    filename = (
        DATA
        / 'XLEFReaderForBioformats'
        / 'annotated stage experiments'
        / 'XLEF-LOF annotated stage experiments'
        / '2021_12_10_14_45_37--XYCST'
        / 'XYCST.lof'
    )

    with LifFile(filename, mode='r', squeeze=True) as lof:
        assert lof.type == LifFileType.LOF
        str(lof)
        assert lof.parent is None
        assert lof.filename == str(filename.name)
        assert lof.dirname == str(filename.parent)
        assert lof.name == 'XYCST'
        assert lof.version == 2
        assert isinstance(lof.xml_element, ElementTree.Element)

        assert lof.xml_header().startswith(
            '<LMSDataContainerHeader Version="2">'
        )

        series = lof.images
        str(series)
        assert isinstance(series, LifImageSeries)
        assert len(series) == 1

        for image in series:
            assert image.path == image.name
            assert isinstance(image, LifImageABC)
            assert isinstance(image, LifImage)

        images = series.findall('XYCST', flags=re.IGNORECASE)
        assert len(images) == 1
        assert images[0].name == 'XYCST'

        im = series[0]
        str(im)
        assert series[im.path] is im
        assert series[im.name + '$'] is im
        assert im.parent is lof
        assert im.name == 'XYCST'
        assert im.path == 'XYCST'
        assert im.uuid == '7949fec1-59bf-11ec-9875-a4bb6dd99fac'
        assert im.parent_image is None
        assert im.child_images == ()
        assert len(im.xml_element) > 0
        assert im.dtype == numpy.uint8
        assert im.itemsize == 1
        assert im.shape == (2, 4, 3, 1200, 1600)
        assert im.dims == ('T', 'M', 'C', 'Y', 'X')
        assert im.sizes == {'T': 2, 'M': 4, 'C': 3, 'Y': 1200, 'X': 1600}
        assert_array_equal(im.coords['C'], ['Ch0', 'Ch1', 'Ch2'])
        assert_allclose(im.coords['T'][[0, -1]], [0.0, 1.0])
        assert_allclose(im.coords['Y'][[0, -1]], [0.0, 0.00122755], atol=1e-4)
        assert_allclose(im.coords['X'][[0, -1]], [0.0, 0.00163707], atol=1e-4)
        assert im.attrs['path'] == im.path
        assert im.timestamps is not None
        assert len(im.timestamps) == 24
        assert im.timestamps[0] == numpy.datetime64('2021-12-10T11:53:16.792')
        assert im.size == 46080000
        assert im.nbytes == 46080000
        assert im.ndim == 5
        assert isinstance(im.xml_element, ElementTree.Element)

        assert im.tilescan is not None
        assert not im.tilescan.flip_x
        assert not im.tilescan.flip_y
        assert not im.tilescan.swap_xy
        assert len(im.tilescan) == len(im.coords['M'])
        for m in im.coords['M']:
            assert im.tilescan[m][-1] == im.tilescan.tiles[m]['pos_x']
            assert im.tilescan['pos_y'][m] == im.tilescan.tiles['pos_y'][m]

        attrs = im.attrs['HardwareSetting']
        assert attrs['Software'] == 'LAS X [ BETA ] 5.0.3.24880'

        data = im.asarray(mode='r', out='memmap')
        assert isinstance(data, numpy.memmap), type(data)
        assert data.sum(dtype=numpy.uint64) == 1456570356

        xdata = im.asxarray(mode='r', out=None)
        assert isinstance(xdata, xarray.DataArray)
        assert_array_equal(xdata.data, data)
        assert xdata.name == im.name
        assert xdata.dtype == im.dtype
        assert xdata.dims == im.dims
        assert xdata.shape == im.shape
        assert xdata.attrs == im.attrs
        assert_array_equal(xdata.coords['T'], im.coords['T'])

        memory_block = im.memory_block
        str(im.memory_block)
        assert isinstance(memory_block, LifMemoryBlock)
        assert memory_block.id == 'MemBlock_1199'
        assert memory_block.offset == 62
        assert memory_block.size == 46080000
        assert memory_block.type == LifMemoryBlockType.MEM
        assert memory_block.read() == data.tobytes()

        _assert_frames(im, xdata.data)


@pytest.mark.parametrize(
    ('name', 'block_type'),
    [
        ('16_18--Proj_LOF001', LifMemoryBlockType.LOF),  # old-style LOF
        ('19_37--Proj_TIF_uncompressed001', LifMemoryBlockType.TIF),
        ('20_09--Proj_TIF_lossless001', LifMemoryBlockType.TIF),
        ('20_38--Proj_BMP001', LifMemoryBlockType.BMP),
        ('21_19--Proj_JPEG_Quality_60%001', LifMemoryBlockType.JPG),
        ('21_51--Proj_PNG001', LifMemoryBlockType.PNG),
    ],
)
def test_xlif(name, block_type):
    """Test XLIF file."""
    filename = (
        DATA
        / 'Leica_Image_File_Format Examples_2015_08'
        / f'2015_03_16_14_{name}'
        / 'Collection ZStack/Metadata'
        / 'ImageXYZ10C2.xlif'
    )

    with LifFile(filename, mode='r', squeeze=True) as xlif:
        assert xlif.type == LifFileType.XLIF
        str(xlif)
        assert xlif.parent is None
        assert xlif.filehandle.closed
        assert xlif.filename == str(filename.name)
        assert xlif.dirname == str(filename.parent)
        assert xlif.name == 'ImageXYZ10C2'
        assert xlif.version == 2
        assert isinstance(xlif.xml_element, ElementTree.Element)

        assert xlif.xml_header().startswith('<?xml version="1.0"?>')
        assert xlif.filehandle.closed

        assert len(xlif.children) == 0

        series = xlif.images
        str(series)
        assert isinstance(series, LifImageSeries)
        assert len(series) == 1

        for image in series:
            str(image)
            assert image.path == image.name
            assert isinstance(image, LifImageABC)
            assert isinstance(image, LifImage)

        images = series.findall('ImageXYZ10C2', flags=re.IGNORECASE)
        assert len(images) == 1
        assert images[0].name == 'ImageXYZ10C2'

        im = series[0]
        str(im)
        assert series[im.path] is im
        assert series[im.name + '$'] is im
        assert im.parent is xlif
        assert im.name == 'ImageXYZ10C2'
        assert im.path == 'ImageXYZ10C2'
        # assert im.uuid == '2b165f65-cbdf-11e4-96dc-bc305be49d23'
        assert len(im.xml_element) > 0
        assert im.dtype == numpy.uint8
        assert im.itemsize == 1
        assert im.shape == (10, 2, 512, 512)
        assert im.dims == ('Z', 'C', 'Y', 'X')
        assert im.sizes == {'Z': 10, 'C': 2, 'Y': 512, 'X': 512}
        assert_array_equal(im.coords['C'], ['Ch0', 'Ch1'])
        assert_allclose(
            im.coords['Z'][[0, -1]], [-2.345302e-05, 1.786591e-05], atol=1e-4
        )
        assert_allclose(
            im.coords['Y'][[0, -1]], [8.673617e-20, 1.162500e-03], atol=1e-4
        )
        assert_allclose(
            im.coords['X'][[0, -1]], [8.673617e-20, 1.162500e-03], atol=1e-4
        )
        assert im.attrs['path'] == im.path
        assert im.timestamps is not None
        assert len(im.timestamps) == 20
        assert im.timestamps[0] == numpy.datetime64('2015-01-27T10:14:30.304')
        assert im.size == 5242880
        assert im.nbytes == 5242880
        assert im.ndim == 4
        assert isinstance(im.xml_element, ElementTree.Element)

        attrs = im.attrs['HardwareSetting']
        assert attrs['Software'] == 'LAS-AF [ BETA ] 1.8.0.12889'

        data = im.asarray(mode='r', out='memmap')
        assert isinstance(data, numpy.memmap), type(data)
        if 'JPEG' not in name:
            assert data.sum(dtype=numpy.uint64) == 80177798

        xdata = im.asxarray(mode='r', out=None)
        assert isinstance(xdata, xarray.DataArray)
        assert_array_equal(xdata.data, data)
        assert xdata.name == im.name
        assert xdata.dtype == im.dtype
        assert xdata.dims == im.dims
        assert xdata.shape == im.shape
        assert xdata.attrs == im.attrs
        assert_array_equal(xdata.coords['Z'], im.coords['Z'])

        memory_block = im.memory_block
        str(im.memory_block)
        assert isinstance(memory_block, LifMemoryBlock)
        assert memory_block.id == ''
        assert memory_block.offset == -1
        assert memory_block.size == 5242880
        assert memory_block.type == block_type
        assert memory_block.read() == data.tobytes()

        _assert_frames(im, xdata.data)


@pytest.mark.parametrize('name', ['LOF', 'TIF'])
def test_xlif_lof(name):
    """Test XLIF file referencing LOF."""
    filename = (
        DATA
        / 'XLEFReaderForBioformats/rgb channel test'
        / f'XLEF-{name} rgb channel test/Metadata'
        / 'z then lambda.xlif'
    )

    with LifFile(filename, mode='r', squeeze=True) as xlif:
        assert xlif.type == LifFileType.XLIF
        str(xlif)

        image = xlif.images[0]
        str(image)

        assert image.memory_block.type == (
            LifMemoryBlockType.LOF if name == 'LOF' else LifMemoryBlockType.TIF
        )

        xdata = image.asxarray(mode='r', out='memmap')
        assert isinstance(xdata, xarray.DataArray)
        assert isinstance(xdata.data, numpy.memmap), type(xdata.data)
        assert xdata.name == 'z then lambda'
        assert xdata.dtype == numpy.uint8
        assert xdata.sizes == {
            'T': 3,
            'C': 2,
            'Z': 5,
            'Y': 1200,
            'X': 1600,
            'S': 3,
        }
        assert xdata.values.sum(dtype=numpy.uint64) == 6270530156

        _assert_frames(image, xdata.data)

        assert len(xlif.children) == 1
        xlif.close()
        for child in xlif.children:
            assert child.filehandle.closed


@pytest.mark.parametrize('name', ['LOF', 'TIF'])
def test_xlef(name):
    """Test XLEF file with XLIF and XLCF children."""
    if name == 'LOF':
        name = 'XLEF-LOF Snail/Schnecke.xlef'
    else:
        name = 'XLEF-TIF Snail/XLEF-TIF Snail.xlef'
    filename = DATA / 'XLEFReaderForBioformats/Snail' / name

    with LifFile(filename, mode='r', squeeze=True) as xlef:
        assert xlef.type == LifFileType.XLEF
        assert xlef.parent is None
        str(xlef)
        assert xlef.filehandle.closed
        assert xlef.filename == str(filename.name)
        assert xlef.dirname == str(filename.parent)
        assert xlef.name == os.path.basename(filename)
        assert xlef.version == 2
        assert isinstance(xlef.xml_element, ElementTree.Element)

        assert xlef.xml_header().startswith('<?xml version="1.0"')
        assert xlef.filehandle.closed

        assert len(xlef.children) == 5

        series = xlef.images
        str(series)
        assert isinstance(series, LifImageSeries)
        assert len(series) == 5

        for image in series:
            str(image)
            assert image.path.endswith(image.name)
            assert isinstance(image, LifImageABC)
            assert isinstance(image, LifImage)

        images = series.findall('Series010_EDF001', flags=re.IGNORECASE)
        assert len(images) == 2
        assert images[0].name == 'Depth Map Image'

        im = series[1]
        str(im)
        assert series[im.path] is im
        assert series[im.name + '$'] is im
        assert im.parent.parent.parent is xlef
        assert im.parent.parent.type == LifFileType.XLCF
        assert im.parent.parent.name == 'Series010_EDF001'
        assert len(im.parent.parent.children) == 2
        assert im.parent.type == LifFileType.XLIF
        assert im.parent.name == 'EDF Image'
        assert im.name == 'EDF Image'
        assert im.path == 'Series010_EDF001/EDF Image'
        assert im.uuid == '67aba58d-b745-11e4-941f-028037ec0200'
        assert len(im.xml_element) == 3
        assert im.dtype == numpy.uint8
        assert im.itemsize == 1
        assert im.sizes == {'Y': 1119, 'X': 1477, 'S': 3}
        assert im.attrs['path'] == im.path
        assert im.timestamps is None
        assert im.size == 4958289
        assert im.nbytes == 4958289
        assert im.ndim == 3
        assert isinstance(im.xml_element, ElementTree.Element)

        data = im.asarray()
        assert isinstance(data, numpy.ndarray)
        rgb = data.sum(dtype=numpy.uint64, axis=(0, 1)).tolist()
        assert rgb == [146107764, 141298533, 133919392]

        assert im.memory_block.type == (
            LifMemoryBlockType.LOF if 'LOF' in name else LifMemoryBlockType.TIF
        )
        if im.memory_block.type == LifMemoryBlockType.LOF:
            assert im._lof_reference is not None
            assert not im._lof_reference.filehandle.closed

        _assert_frames(im, data)

        xdata = im.asxarray()
        assert isinstance(xdata, xarray.DataArray)
        assert_array_equal(xdata.data, data)


def test_xlef_tmczyx():
    """Test XLEF file with TMCZYX dimensions."""
    filename = DATA / 'XYZCST/XYZCST.xlef'  # M dimension is S in LASX

    with LifFile(filename, mode='r', squeeze=True) as xlef:
        assert xlef.type == LifFileType.XLEF
        assert xlef.parent is None
        str(xlef)
        assert xlef.filehandle.closed
        assert xlef.filename == str(filename.name)
        assert xlef.dirname == str(filename.parent)
        assert xlef.name == os.path.basename(filename)
        assert xlef.version == 2
        assert isinstance(xlef.xml_element, ElementTree.Element)

        assert xlef.xml_header().startswith('<?xml version="1.0"')
        assert xlef.filehandle.closed

        assert len(xlef.children) == 2

        series = xlef.images
        str(series)
        assert isinstance(series, LifImageSeries)
        assert len(series) == 1

        im = series[0]
        str(im)
        assert isinstance(im, LifImage)
        assert series[im.path] is im
        assert series[im.name + '$'] is im
        assert im.parent.parent is xlef
        assert im.parent.type == LifFileType.XLIF
        assert im.parent.name == 'XYZCST'
        assert len(im.parent.children) == 0
        assert im.name == 'XYZCST'
        assert im.path == 'XYZCST'
        assert im.uuid == '5ec11c49-59bf-11ec-9875-a4bb6dd99fac'
        assert len(im.xml_element) == 4
        assert im.dtype == numpy.uint8
        assert im.itemsize == 1
        assert im.sizes == {
            'T': 2,
            'M': 4,
            'C': 3,
            'Z': 5,
            'Y': 1200,
            'X': 1600,
        }
        assert im.attrs['path'] == im.path
        assert im.timestamps is not None
        assert len(im.timestamps) == 120
        assert im.size == 230400000
        assert im.nbytes == 230400000
        assert im.ndim == 6
        assert isinstance(im.xml_element, ElementTree.Element)

        assert im.tilescan is not None
        assert not im.tilescan.flip_x
        assert not im.tilescan.flip_y
        assert not im.tilescan.swap_xy
        assert len(im.tilescan) == len(im.coords['M'])
        for m in im.coords['M']:
            assert im.tilescan[m][-1] == im.tilescan.tiles[m]['pos_x']
            assert im.tilescan['pos_z'][m] == im.tilescan.tiles['pos_z'][m]

        data = im.asarray()
        assert isinstance(data, numpy.ndarray)
        checksum = data.sum(dtype=numpy.uint64, axis=(0, 1, 3, 4, 5)).tolist()
        assert checksum == [2704560639, 2603036403, 2544171284]

        assert im.memory_block.type == LifMemoryBlockType.LOF
        assert im._lof_reference is not None
        assert not im._lof_reference.filehandle.closed

        _assert_frames(im, data)

        xdata = im.asxarray()
        assert isinstance(xdata, xarray.DataArray)
        assert_array_equal(xdata.data, data)


def test_lifext():
    """Test LIFEXT file."""
    filename = str(DATA / 'XLEFReaderForBioformats/dimension tests LIFs/XYZCS')

    with (
        LifFile(filename + '.lif') as parent,
        LifFile(filename + '.lifext', _parent=parent) as lifext,
    ):
        assert lifext.type == LifFileType.LIFEXT
        str(lifext)
        assert lifext.parent is parent
        assert lifext.filename == 'XYZCS.lifext'
        assert not lifext.filehandle.closed
        assert lifext.name == 'XYZCS.lifext'
        assert lifext.version == 1
        assert lifext.uuid is None
        assert lifext.datetime is None
        assert len(lifext.memory_blocks) == 7
        assert isinstance(lifext.xml_element, ElementTree.Element)
        assert repr(lifext).startswith('<LifFile ')
        assert lifext.xml_header().startswith(
            '<LMSDataContainerEnhancedHeader Version="1">'
        )

        series = lifext.images
        str(series)
        assert isinstance(series, LifImageSeries)
        assert len(series) == 7
        with pytest.raises(IndexError):
            lifext.images[8]

        for image in series:
            str(image)
            assert isinstance(image, LifImageABC)
            assert isinstance(image, LifImage)

        images = series.findall('XYZCS_pmd_0.*', flags=re.IGNORECASE)
        assert len(images) == 6

        im = images[0]
        assert im.name == 'XYZCS_pmd_0'
        assert im.parent_image is parent.images[0]
        assert im.parent_image.child_images == ()  # TODO == (im,)
        assert im.child_images == (images[1],)

        im = series[1]
        str(im)
        assert series[im.path] is im
        assert series[im.name + '$'] is im
        assert im.parent is lifext
        assert im.name == 'XYZCS_pmd_1'
        assert im.path == 'MemBlock_836/XYZCS_pmd_0/XYZCS_pmd_1'
        assert im.uuid == '2e0b0305-599f-11ec-9875-a4bb6dd99fac'
        assert len(im.xml_element) > 0
        assert im.dtype == numpy.uint8
        assert im.itemsize == 1
        assert im.sizes == {'M': 4, 'C': 2, 'Z': 5, 'Y': 300, 'X': 400}
        assert_array_equal(im.coords['C'], ['Ch0', 'Ch1'])
        assert_allclose(im.coords['Z'][[0, -1]], [0.0, 7.19784e-05])
        assert im.attrs['path'] != im.parent.name + '/' + im.path
        assert im.timestamps is None
        assert im.size == 4800000
        assert im.nbytes == 4800000
        assert im.ndim == 5
        assert isinstance(im.xml_element, ElementTree.Element)

        data = im.asarray(mode='r', out='memmap')
        assert isinstance(data, numpy.memmap), type(data)
        assert data.sum(dtype=numpy.uint64) == 180034506

        _assert_frames(im, data)

        xdata = im.asxarray(mode='r', out=None)
        assert isinstance(xdata, xarray.DataArray)
        assert_array_equal(xdata.data, data)
        assert xdata.name == im.name
        assert xdata.dtype == im.dtype
        assert xdata.dims == im.dims
        assert xdata.shape == im.shape
        assert xdata.attrs == im.attrs

        memory_block = im.memory_block
        str(im.memory_block)
        assert isinstance(memory_block, LifMemoryBlock)
        assert memory_block.id == 'MemBlock_838'
        assert memory_block.offset == 19222545
        assert memory_block.size == 4800000
        assert memory_block.type == LifMemoryBlockType.MEM
        assert memory_block.read() == data.tobytes()


@pytest.mark.parametrize('index', range(len(SCANMODES)))
def test_scan_modes(index, scanmodes_file):
    """Test scan modes."""
    path, sizes, dtype = SCANMODES[index]
    shape = tuple(sizes.values())
    with LifFile(scanmodes_file, squeeze=False) as lif:
        image = lif.images[index]
        assert image.path == path
        assert image.sizes == sizes
        assert image.shape == shape
        assert image.dtype == dtype
        assert image.timestamps is not None
        data = image.asxarray()
        assert data.shape == shape
        assert data.dtype == dtype

        _assert_frames(image, data.data)

    if 1 in sizes.values():
        sizes = {k: v for k, v in sizes.items() if v > 1}
        shape = tuple(sizes.values())
        with LifFile(scanmodes_file) as lif:
            image = lif.images[index]
            assert image.path == path
            assert image.sizes == sizes
            assert image.shape == shape
            assert image.dtype == dtype
            data = image.asxarray()
            assert data.shape == shape
            assert data.dtype == dtype

            _assert_frames(image, data.data)


def test_frame_indices_errors(scanmodes_file):
    """Test frames selection raises appropriate errors."""
    with LifFile(scanmodes_file) as lif:
        # use XYZT which has T, Z, C dimensions outside frame
        image = lif.images['XYZT']
        assert 'T' in image.sizes
        assert 'Z' in image.sizes

        # unknown dimension raises KeyError
        with pytest.raises(KeyError):
            image.frames(Q=0)

        # out of bounds index raises IndexError
        # (triggers when accessing _info)
        with pytest.raises(IndexError):
            len(image.frames(T=100))

        # out of bounds in sequence raises IndexError
        # (triggers when accessing _info)
        with pytest.raises(IndexError):
            len(image.frames(T=[0, 100]))


@pytest.mark.parametrize(
    ('name', 'expected_frame_dims'),
    [
        # ZX frame (no Y dimension)
        ('Mark_and_Find_XZLambdaT/Position7007', ('Z', 'X')),
        ('SequenceLambda/Job_XZL096', ('Z', 'X')),
        ('Mark_and_Find_XZT/Position7007', ('Z', 'X')),
        # TX frame (time-space)
        ('Mark_and_Find_XT/Position7007', ('T', 'X')),
    ],
)
def test_frame_dims_unusual(scanmodes_file, name, expected_frame_dims):
    """Test frame_dims for unusual dimension orders (ZX, TX instead of YX)."""
    with LifFile(scanmodes_file, squeeze=True) as lif:
        image = lif.images[name]
        frame_dims = image.frames.frame_dims
        assert frame_dims == expected_frame_dims
        assert len(frame_dims) == 2
        _assert_frames(image, image.asarray())


def test_frame_method():
    """Test frame method returns correct single frames."""
    filename = DATA / 'image.sc_107410/Edu_examples.lif'
    with LifFile(filename) as lif:
        image = lif.images[0]
        data = image.asarray()

        assert image.sizes == {'C': 4, 'Z': 10, 'Y': 1024, 'X': 1024}

        # test default indices (all zeros)
        frame = image.frame()
        assert frame.shape == (1024, 1024)
        assert_array_equal(frame, data[0, 0])

        # test specified indices
        frame = image.frame(C=1, Z=3)
        assert frame.shape == (1024, 1024)
        assert_array_equal(frame, data[1, 3])

        # test partial indices (unspecified default to 0)
        frame = image.frame(Z=5)
        assert_array_equal(frame, data[0, 5])

        # test out parameter
        out = numpy.zeros((1024, 1024), dtype=image.dtype)
        result = image.frame(C=2, Z=7, out=out)
        assert result is out
        assert_array_equal(result, data[2, 7])

        # test errors
        with pytest.raises(KeyError):
            image.frame(Q=0)

        with pytest.raises(IndexError):
            image.frame(C=100)


def test_frames_iteration_order():
    """Test frames() iteration order follows keyword argument order."""
    filename = DATA / 'image.sc_107410/Edu_examples.lif'
    with LifFile(filename) as lif:
        image = lif.images[0]
        frames = image.frames

        assert image.ndim == 4
        assert image.dims == ('C', 'Z', 'Y', 'X')
        assert image.shape == (4, 10, 1024, 1024)

        assert frames.ndim == 4
        assert frames.dims == ('C', 'Z', 'Y', 'X')
        assert frames.shape == (4, 10, 1024, 1024)
        assert frames is frames()  # no selection returns self

        # default order: natural dimension order (C, Z)
        # dims = ('C', 'Z'), so tuple is (C_idx, Z_idx)
        indices_default = list(frames.keys())
        assert indices_default[0] == (0, 0)  # C=0, Z=0
        assert indices_default[1] == (0, 1)  # C=0, Z=1
        assert indices_default[10] == (1, 0)  # C=1, Z=0

        # specify Z first, then C: unspecified=[], specified=['Z', 'C']
        # dims = ('Z', 'C'), so tuple is (Z_idx, C_idx)
        frames_zc = frames(Z=None, C=None)
        indices_zc = list(frames_zc.keys())
        assert frames_zc is not frames  # selection returns new object
        assert frames_zc.shape == (10, 4, 1024, 1024)
        assert frames_zc.dims == ('Z', 'C', 'Y', 'X')
        assert frames_zc._info.dims == ('Z', 'C')
        assert indices_zc[0] == (0, 0)  # Z=0, C=0
        assert indices_zc[1] == (0, 1)  # Z=0, C=1
        assert indices_zc[4] == (1, 0)  # Z=1, C=0

        # specify C first, then Z: unspecified=[], specified=['C', 'Z']
        # dims = ('C', 'Z'), same as default
        frames_cz = frames(C=None, Z=None)
        indices_cz = list(frames_cz.keys())
        assert frames_cz.shape == (4, 10, 1024, 1024)
        assert frames_cz.dims == ('C', 'Z', 'Y', 'X')
        assert frames_cz._info.dims == ('C', 'Z')
        assert indices_cz == indices_default

        # specify only Z: unspecified=['C'], specified=['Z']
        # dims = ('C', 'Z'), same as default
        frames_z_only = frames(Z=None)
        indices_z_only = list(frames_z_only.keys())
        assert frames_z_only.shape == (4, 10, 1024, 1024)
        assert frames_z_only.dims == ('C', 'Z', 'Y', 'X')
        assert frames_z_only._info.dims == ('C', 'Z')
        assert indices_z_only == indices_default

        # specify only C: unspecified=['Z'], specified=['C']
        # dims = ('Z', 'C'), so tuple is (Z_idx, C_idx)
        frames_c_only = frames(C=None)
        indices_c_only = list(frames_c_only.keys())
        assert frames_c_only.shape == (10, 4, 1024, 1024)
        assert frames_c_only.dims == ('Z', 'C', 'Y', 'X')
        assert frames_c_only._info.dims == ('Z', 'C')
        assert indices_c_only[0] == (0, 0)  # Z=0, C=0
        assert indices_c_only[1] == (0, 1)  # Z=0, C=1
        assert indices_c_only[4] == (1, 0)  # Z=1, C=0


def test_frames_selection_types():
    """Test frames() with different selection types."""
    filename = DATA / 'image.sc_107410/Edu_examples.lif'
    with LifFile(filename) as lif:
        image = lif.images[0]
        frames = image.frames
        data = image.asarray()

        assert image.ndim == 4
        assert image.dims == ('C', 'Z', 'Y', 'X')
        assert image.shape == (4, 10, 1024, 1024)

        assert frames.ndim == 4
        assert frames.dims == ('C', 'Z', 'Y', 'X')
        assert frames.shape == (4, 10, 1024, 1024)

        # check that image has coords for spatial and channel dimensions
        assert 'Y' in image.coords
        assert 'X' in image.coords
        assert 'Z' in image.coords
        assert len(image.coords['Z']) == 10
        assert len(image.coords['Y']) == 1024
        assert len(image.coords['X']) == 1024
        assert_array_equal(
            image.coords['C'],
            ['ALEXA 405', 'ALEXA 488', 'ALEXA 488', 'ALEXA 555'],
        )

        # full frames should have same coords
        assert 'Y' in frames.coords
        assert 'X' in frames.coords
        assert 'Z' in frames.coords
        assert_array_equal(frames.coords['Z'], image.coords['Z'])
        assert_array_equal(frames.coords['Y'], image.coords['Y'])
        assert_array_equal(frames.coords['X'], image.coords['X'])

        # int selection (fixed index)
        # C is fixed at 1, only Z iterates
        # dims = ('Z',), so tuple is (Z_local_idx,)
        frames_c1 = image.frames(C=1)
        assert len(frames_c1) == 10  # all Z values
        assert frames_c1.ndim == 3
        assert frames_c1.shape == (10, 1024, 1024)
        assert frames_c1.dims == ('Z', 'Y', 'X')
        assert frames_c1._info.dims == ('Z',)
        assert frames_c1 is not frames  # selection returns new object
        # coords should be indexed: Z has all values, Y and X unchanged
        assert_array_equal(frames_c1.coords['Z'], image.coords['Z'])
        assert_array_equal(frames_c1.coords['Y'], image.coords['Y'])
        assert_array_equal(frames_c1.coords['X'], image.coords['X'])
        for i, (nd_idx, frame) in enumerate(frames_c1.items()):
            assert nd_idx == (i,)  # local index
            # Convert to global: C=1 (fixed), Z=i (iterates 0..9)
            assert_array_equal(frame, data[1, i])

        # slice selection
        # Both C and Z specified with slices
        # dims = ('C', 'Z') since C specified first
        # Local indices are (C_local, Z_local) where both start from 0
        frames_slice = image.frames(C=slice(0, 2), Z=slice(2, 5))
        assert len(frames_slice) == 6  # 2 * 3
        assert frames_slice.shape == (2, 3, 1024, 1024)
        assert frames_slice.dims == ('C', 'Z', 'Y', 'X')
        assert frames_slice._info.dims == ('C', 'Z')
        # coords should be sliced: Z has indices 2:5, Y and X unchanged
        assert len(frames_slice.coords['Z']) == 3
        assert_array_equal(frames_slice.coords['Z'], image.coords['Z'][2:5])
        assert_array_equal(frames_slice.coords['Y'], image.coords['Y'])
        assert_array_equal(frames_slice.coords['X'], image.coords['X'])
        expected_indices = [
            (0, 0),  # C_local=0 (C_global=0), Z_local=0 (Z_global=2)
            (0, 1),  # C_local=0 (C_global=0), Z_local=1 (Z_global=3)
            (0, 2),  # C_local=0 (C_global=0), Z_local=2 (Z_global=4)
            (1, 0),  # C_local=1 (C_global=1), Z_local=0 (Z_global=2)
            (1, 1),  # C_local=1 (C_global=1), Z_local=1 (Z_global=3)
            (1, 2),  # C_local=1 (C_global=1), Z_local=2 (Z_global=4)
        ]
        assert list(frames_slice.keys()) == expected_indices

        # sequence selection
        z_indices = [9, 5, 2, 0]
        # C is fixed at 0, Z iterates through sequence
        # dims = ('Z',)
        frames_seq = image.frames(C=0, Z=z_indices)
        assert len(frames_seq) == 4
        assert frames_seq.shape == (4, 1024, 1024)
        assert frames_seq.dims == ('Z', 'Y', 'X')
        assert frames_seq._info.dims == ('Z',)
        # coords should be indexed by sequence: Z has indices [9, 5, 2, 0]
        assert len(frames_seq.coords['Z']) == 4
        assert_array_equal(
            frames_seq.coords['Z'], image.coords['Z'][z_indices]
        )
        assert_array_equal(frames_seq.coords['Y'], image.coords['Y'])
        assert_array_equal(frames_seq.coords['X'], image.coords['X'])
        for i, (nd_idx, frame) in enumerate(frames_seq.items()):
            assert nd_idx == (i,)  # local index 0, 1, 2, 3
            # Global Z index from sequence
            assert_array_equal(frame, data[0, z_indices[i]])

        # None selection (iterate all)
        assert len(image.frames(C=None)) == len(image.frames)

        # mixed selection
        # C fixed at 1, Z iterates through sequence
        # dims = ('Z',)
        frames_mixed = image.frames(C=1, Z=[2, 5, 7])
        assert len(frames_mixed) == 3
        assert frames_mixed.shape == (3, 1024, 1024)
        assert frames_mixed.dims == ('Z', 'Y', 'X')
        assert frames_mixed._info.dims == ('Z',)
        # coords should be indexed by sequence: Z has indices [2, 5, 7]
        assert len(frames_mixed.coords['Z']) == 3
        assert_array_equal(
            frames_mixed.coords['Z'], image.coords['Z'][[2, 5, 7]]
        )
        assert_array_equal(frames_mixed.coords['Y'], image.coords['Y'])
        assert_array_equal(frames_mixed.coords['X'], image.coords['X'])
        expected_mixed = [
            (0,),  # Z_local=0 (Z_global=2)
            (1,),  # Z_local=1 (Z_global=5)
            (2,),  # Z_local=2 (Z_global=7)
        ]
        assert list(frames_mixed.keys()) == expected_mixed


def test_frames_get_method():
    """Test frames.get() method with default values."""
    filename = DATA / 'image.sc_107410/Edu_examples.lif'
    with LifFile(filename) as lif:
        image = lif.images[0]
        data = image.asarray()
        frames = image.frames

        # valid linear index returns frame
        frame = frames.get(0)
        assert frame is not None
        assert_array_equal(frame, data[0, 0])

        # valid ND tuple index returns frame
        frame = frames.get((1, 5))
        assert frame is not None
        assert_array_equal(frame, data[1, 5])

        # out of bounds linear index returns default
        result = frames.get(999)
        assert result is None

        # out of bounds linear index with custom default
        default_arr = numpy.zeros((10, 10))
        result = frames.get(999, default=default_arr)
        assert result is default_arr

        # out of bounds ND index returns default
        result = frames.get((100, 100))
        assert result is None

        # wrong length ND index returns default
        result = frames.get((1, 2, 3))
        assert result is None

        # invalid type returns default
        result = frames.get('invalid')
        assert result is None

        # custom default value
        custom_default = numpy.array([42])
        result = frames.get(999, default=custom_default)
        assert result is custom_default

        # test with selection
        frames_sub = image.frames(C=1)
        frame = frames_sub.get(0)
        assert frame is not None
        assert_array_equal(frame, data[1, 0])

        result = frames_sub.get(100)
        assert result is None


def test_frames_unravel_ravel():
    """Test unravel_index and ravel_multi_index methods."""
    filename = DATA / 'image.sc_107410/Edu_examples.lif'
    with LifFile(filename) as lif:
        image = lif.images[0]
        # image.sizes = {'C': 4, 'Z': 10, 'Y': 1024, 'X': 1024}
        frames = image.frames

        # test unravel_index with local indices
        nd_idx = frames.unravel_index(0, global_=False)
        assert nd_idx == (0, 0)  # C=0, Z=0

        nd_idx = frames.unravel_index(1, global_=False)
        assert nd_idx == (0, 1)  # C=0, Z=1

        nd_idx = frames.unravel_index(10, global_=False)
        assert nd_idx == (1, 0)  # C=1, Z=0

        nd_idx = frames.unravel_index(39, global_=False)
        assert nd_idx == (3, 9)  # C=3, Z=9 (last frame)

        # test unravel_index with global indices (same as local here)
        nd_idx = frames.unravel_index(0, global_=True)
        assert nd_idx == (0, 0)

        nd_idx = frames.unravel_index(39, global_=True)
        assert nd_idx == (3, 9)

        # test ravel_multi_index with local indices
        linear = frames.ravel_multi_index((0, 0), global_=False)
        assert linear == 0

        linear = frames.ravel_multi_index((0, 1), global_=False)
        assert linear == 1

        linear = frames.ravel_multi_index((1, 0), global_=False)
        assert linear == 10

        linear = frames.ravel_multi_index((3, 9), global_=False)
        assert linear == 39

        # test ravel_multi_index with global indices (same as local here)
        linear = frames.ravel_multi_index((0, 0), global_=True)
        assert linear == 0

        linear = frames.ravel_multi_index((3, 9), global_=True)
        assert linear == 39

        # test round-trip conversion
        for i in range(len(frames)):
            nd_local = frames.unravel_index(i, global_=False)
            linear_back = frames.ravel_multi_index(nd_local, global_=False)
            assert linear_back == i

            nd_global = frames.unravel_index(i, global_=True)
            linear_back = frames.ravel_multi_index(nd_global, global_=True)
            assert linear_back == i

        # test with slice selection
        frames_slice = image.frames(C=slice(1, 3), Z=slice(2, 5))
        # Local shape: (2, 3) for C and Z
        # Global: C=[1,2], Z=[2,3,4]

        # local index (0, 0) -> global (1, 2)
        nd_local = frames_slice.unravel_index(0, global_=False)
        assert nd_local == (0, 0)
        nd_global = frames_slice.unravel_index(0, global_=True)
        assert nd_global == (1, 2)

        # local index (1, 2) -> global (2, 4)
        nd_local = frames_slice.unravel_index(5, global_=False)
        assert nd_local == (1, 2)
        nd_global = frames_slice.unravel_index(5, global_=True)
        assert nd_global == (2, 4)

        # ravel with local indices
        linear = frames_slice.ravel_multi_index((0, 0), global_=False)
        assert linear == 0

        linear = frames_slice.ravel_multi_index((1, 2), global_=False)
        assert linear == 5

        # ravel with global indices
        linear = frames_slice.ravel_multi_index((1, 2), global_=True)
        assert linear == 0

        linear = frames_slice.ravel_multi_index((2, 4), global_=True)
        assert linear == 5

        # test with sequence selection
        frames_seq = image.frames(C=0, Z=[9, 5, 2, 0])
        # Local shape: (4,) for Z
        # Global: Z=[9, 5, 2, 0]

        nd_local = frames_seq.unravel_index(0, global_=False)
        assert nd_local == (0,)
        nd_global = frames_seq.unravel_index(0, global_=True)
        assert nd_global == (9,)

        nd_local = frames_seq.unravel_index(3, global_=False)
        assert nd_local == (3,)
        nd_global = frames_seq.unravel_index(3, global_=True)
        assert nd_global == (0,)

        linear = frames_seq.ravel_multi_index((0,), global_=False)
        assert linear == 0

        linear = frames_seq.ravel_multi_index((9,), global_=True)
        assert linear == 0

        linear = frames_seq.ravel_multi_index((0,), global_=True)
        assert linear == 3

        # test error conditions for unravel_index
        with pytest.raises(IndexError):
            frames.unravel_index(-1, global_=False)

        with pytest.raises(IndexError):
            frames.unravel_index(1000, global_=False)

        # test error conditions for ravel_multi_index
        # wrong length
        with pytest.raises(ValueError):
            frames.ravel_multi_index((0, 0, 0), global_=False)

        # out of bounds local index
        with pytest.raises(IndexError):
            frames.ravel_multi_index((10, 0), global_=False)

        # out of bounds global index
        with pytest.raises(IndexError):
            frames.ravel_multi_index((10, 0), global_=True)

        # global index not in slice range
        with pytest.raises(IndexError):
            frames_slice.ravel_multi_index((0, 0), global_=True)

        # global index not in sequence
        with pytest.raises(IndexError):
            frames_seq.ravel_multi_index((1,), global_=True)


@pytest.mark.parametrize(
    'name',
    [
        'FLIM_testdata.lif',
        'XLEF_LOF/FLIM_testdata.xlef',
        'XLEF_OME/FLIM_testdata.xlef',
        'XLEF_TIF/FLIM_testdata.xlef',
        'XLEF_AIVIA/FLIM_testdata.xlef',
        '../case_sensitive/FLIM_testdata/FLIM_testdata.xlef',
    ],
)
def test_flim(name):
    """Test FLIM image formats."""
    filename = DATA / 'FLIM_testdata' / name
    with LifFile(filename) as lif:
        str(lif)
        for image in lif.images:
            str(image)

        base = lif.images['sample1_slice1']

        flim = lif.images['FLIM Compressed']
        assert isinstance(flim, LifImageABC)
        assert isinstance(flim, LifFlimImage)
        if name.endswith('.lif'):
            assert flim.parent_image is base
        assert len(flim.child_images) == 9
        assert lif.uuid == 'd9f87ad9-b958-11ed-bb27-00506220277a'
        assert flim.is_flim
        assert flim.dtype == numpy.uint16
        assert flim.sizes == {'Y': 1024, 'X': 1024, 'H': 528}
        assert pytest.approx(flim.coords['X'][-1]) == 0.0005563808000453999
        assert pytest.approx(flim.coords['Y'][-1]) == 0.0005563808000453999
        assert pytest.approx(flim.coords['H'][-1]) == 5.110303030319e-08
        assert flim.attrs['path'].endswith('/FLIM Compressed')
        assert flim.attrs['RawData']['LaserPulseFrequency'] == 19505000
        assert flim.global_resolution == 5.126890540886952e-08
        assert flim.tcspc_resolution == 9.696969697e-11
        assert flim.number_bins_in_period == 528
        assert flim.pixel_time == 7.6875e-06
        assert flim.frequency == 19.505
        assert not flim.is_bidirectional
        assert not flim.is_sinusoidal
        assert flim.timestamps is None
        if name == 'XLEF_TIF/FLIM_testdata.xlef':
            # TIFF file is actually a LOF file
            with pytest.raises(RuntimeError):
                flim.memory_block.read()
        else:
            assert len(flim.memory_block.read()) == 15502568
        with pytest.raises(NotImplementedError):
            flim.asxarray()
        with pytest.raises(NotImplementedError):
            _ = flim.frames

        intensity = lif.images['/Intensity']
        assert intensity in flim.child_images
        assert intensity.parent_image is flim
        mbtype = intensity.memory_block.type
        if '.lif' in name:
            assert mbtype == LifMemoryBlockType.MEM
        else:
            assert mbtype == LifMemoryBlockType.LOF

        data = intensity.asxarray()
        assert data.shape == (1024, 1024)
        assert data.dtype == numpy.float32
        assert data.attrs['TileScanInfo']['Tile']['PosX'] == -0.0471300149

        mean = lif.images['Phasor Intensity$']
        assert mean in flim.child_images
        assert mean.parent_image is flim

        data = mean.asxarray()
        assert data.shape == (1024, 1024)
        assert data.dtype == numpy.float16
        assert data.attrs['TileScanInfo']['Tile']['PosX'] == -0.0471300149

        real = lif.images['Phasor Real']
        assert real in flim.child_images
        assert real.parent_image is flim

        mbtype = real.memory_block.type
        if '.lif' in name:
            assert mbtype == LifMemoryBlockType.MEM
        elif 'LOF' in name:
            assert mbtype == LifMemoryBlockType.LOF
        elif 'TIF' in name:
            assert mbtype == LifMemoryBlockType.LOF  # not TIFF
        elif 'AIVIA' in name:
            assert mbtype == LifMemoryBlockType.AIVIA
        elif 'OME' in name:
            assert mbtype == LifMemoryBlockType.OME

        data = real.asxarray()
        assert data.shape == (1024, 1024)
        assert data.dtype == numpy.float16
        assert data.attrs['F16']['FactorF32ToF16'] == 1.0

        lifetime = lif.images['Fast Flim']
        assert lifetime in flim.child_images
        assert lifetime.parent_image is flim

        data = lifetime.asxarray()
        assert data.shape == (1024, 1024)
        assert data.dtype == numpy.float16
        assert data.attrs['F16']['FactorF32ToF16'] == 1000000000.0

        mask = lif.images['Phasor Mask']
        assert mask in flim.child_images
        assert mask.parent_image is flim

        data = mask.asxarray()
        assert data.shape == (1024, 1024)
        assert data.dtype == numpy.uint32
        gamma = data.attrs['ViewerScaling']['ChannelScalingInfo']['GammaValue']
        assert gamma == 1.0


@pytest.mark.parametrize(
    'name',
    [
        'RS_FALCON_10Volumes.lif',
        'RS_FALCON_10Volumes.ome.tif/RS_FALCON_10Volumes.xlef',
    ],
)
def test_flim_nd(name):
    """Test multi-dimensional FLIM image formats."""
    filename = DATA / name
    with LifFile(filename) as lif:
        str(lif)
        assert len(lif.images) == 12
        for image in lif.images:
            str(image)

        base = lif.images['Series006 Crop']
        assert isinstance(base, LifImage)
        assert base.parent_image is None
        assert len(base.child_images) == 1
        assert base.uuid == '2dbe7657-c99c-11ee-b559-98597a5338f0'
        assert not base.is_flim
        assert base.dtype == numpy.uint8
        assert base.sizes == {'T': 10, 'Z': 10, 'C': 2, 'Y': 2048, 'X': 2048}
        if '.xlef' in name:
            assert base.memory_block.type == LifMemoryBlockType.OME
            assert base._tif_reference is not None
            assert not base._tif_reference.filehandle.closed
        else:
            assert base.memory_block.type == LifMemoryBlockType.MEM
            assert base._tif_reference is None

        _assert_frames(base, base.asarray())

        flim = lif.images['Series006$']
        assert isinstance(flim, LifImageABC)
        assert isinstance(flim, LifFlimImage)
        # if name.endswith('.lif'):
        assert flim.parent_image is base
        assert len(flim.child_images) == 10
        assert lif.uuid == '4441a913-c99c-11ee-b559-98597a5338f0'
        assert flim.is_flim
        assert flim.dtype == numpy.uint16
        assert flim.sizes == {
            'T': 10,
            'Z': 10,
            'C': 2,
            'Y': 2048,
            'X': 2048,
            'H': 132,
        }
        assert pytest.approx(flim.coords['X'][-1]) == 6.07900899999e-05
        assert pytest.approx(flim.coords['Y'][-1]) == 6.07900899999e-05
        assert pytest.approx(flim.coords['Z'][-1]) == 2.0256059997000003e-06
        assert pytest.approx(flim.coords['H'][-1]) == 1.270303030307e-08
        assert flim.attrs['path'].endswith('/Series006 Crop/Series006')
        assert flim.attrs['RawData']['LaserPulseFrequency'] == 78020000
        assert flim.global_resolution == 1.281722635221738e-08
        assert flim.tcspc_resolution == 9.696969697e-11
        assert flim.number_bins_in_period == 132
        assert flim.pixel_time == 1.8448e-08
        assert flim.frequency == 78.02
        assert flim.is_bidirectional
        assert not flim.is_sinusoidal
        assert flim.timestamps is None
        assert len(flim.memory_block.read()) == 1004310116
        with pytest.raises(NotImplementedError):
            flim.asxarray()
        with pytest.raises(NotImplementedError):
            _ = flim.frames

        lifetime = lif.images['Fast Flim']
        assert lifetime in flim.child_images
        assert lifetime.parent_image is flim
        data = lifetime.asxarray()
        assert data.shape == (10, 2, 10, 2048, 2048)
        assert data.dtype == numpy.float16
        assert data.attrs['F16']['FactorF32ToF16'] == 1000000000.0
        _assert_frames(lifetime, data.data)


def test_flim_lof():
    """Test LOF file with FLIM image."""
    filename = (
        DATA
        / 'XLEFReaderForBioformats/falcon_sample_data_small'
        / 'XLEF-LOF falcon_sample_data_small/Series003'
        / 'FLIM Compressed.lof'
    )
    with LifFile(filename) as lof:
        str(lof)
        assert lof.type == LifFileType.LOF
        assert lof.uuid == '4a942888-fa9c-11eb-913c-a4bb6dd5b508'
        assert len(lof.images) == 1
        memblock = lof.memory_blocks['MemBlock_1643']
        assert len(memblock.read()) == memblock.size

        for image in lof.images:
            str(image)

        flim = lof.images['FLIM Compressed']
        assert isinstance(flim, LifImageABC)
        assert isinstance(flim, LifFlimImage)
        assert flim.uuid == '4a942888-fa9c-11eb-913c-a4bb6dd5b508'
        assert flim.is_flim
        assert flim.dtype == numpy.uint16
        assert flim.sizes == {'C': 2, 'Y': 512, 'X': 512, 'H': 132}
        assert pytest.approx(flim.coords['X'][-1]) == 0.0011624999998359998
        assert pytest.approx(flim.coords['Y'][-1]) == 0.0011624999998359998
        assert pytest.approx(flim.coords['H'][-1]) == 1.270303030307e-08
        assert flim.attrs['path'].endswith('/FLIM Compressed')
        assert flim.attrs['RawData']['LaserPulseFrequency'] == 78020000
        assert flim.global_resolution == 1.281722635221738e-08
        assert flim.tcspc_resolution == 9.696969697e-11
        assert flim.number_bins_in_period == 132
        assert flim.pixel_time == 3.1625e-06
        assert flim.frequency == 78.02
        assert not flim.is_bidirectional
        assert not flim.is_sinusoidal
        assert flim.timestamps is None
        assert len(flim.memory_block.read()) == 1538370
        with pytest.raises(NotImplementedError):
            flim.asxarray()


def test_rgb():
    """Test read 6 channel RGB."""
    filename = DATA / 'RGB/Experiment.lif'
    with LifFile(filename) as lif:
        image = lif.images[0]
        assert image.sizes == {'C': 2, 'Y': 1536, 'X': 2048, 'S': 3}
        # C=2, S=3 -> 6 channels total; count mismatch so no coords for C or S
        assert 'C' not in image.coords
        assert 'S' not in image.coords
        assert_array_equal(
            image.timestamps,
            numpy.array(
                ['2012-10-12T00:18:10.777', '2012-10-12T00:18:13.798'],
                dtype='datetime64[ms]',
            ),
        )
        data = image.asarray()
        assert_array_equal(
            data.sum(dtype=numpy.uint64, axis=(0, 1, 2)),
            [12387812, 9225469, 82284132],
        )

        frames = image.frames
        assert frames.frame_shape == (1536, 2048, 3)
        assert frames.frame_dims == ('Y', 'X', 'S')
        _assert_frames(image, data)

        image = lif.images[1]
        assert image.sizes == {'Y': 1536, 'X': 2048, 'S': 3}
        assert_array_equal(image.coords['S'], ['Red', 'Green', 'Blue'])
        data = image.asarray()
        assert data.sum(dtype=numpy.uint64) == 86724120

        _assert_frames(image, data)


def test_rgb_pad():
    """Test read RGB with padding at end of rows."""
    filename = DATA / 'image.sc_108815/Cont HIF alpha.lif'
    with LifFile(filename) as lif:
        assert len(lif.images) == 20
        for i, image in enumerate(lif.images):
            frames = image.frames
            assert image.dtype == numpy.uint8
            if i % 4 == 0:
                assert image.sizes == {'C': 2, 'Y': 2048, 'X': 2048}
                assert frames.frame_sizes == {'Y': 2048, 'X': 2048}
                data = image.asxarray()
            elif i == 9:
                assert image.sizes == {'Y': 1075, 'X': 1075, 'S': 3}
                assert frames.frame_sizes == image.sizes
                data = image.asxarray()
                assert data.shape == (1075, 1075, 3)
            else:
                assert image.sizes == {'Y': 531, 'X': 531, 'S': 3}
                assert frames.frame_sizes == image.sizes
                data = image.asxarray()
                assert data.shape == (531, 531, 3)

            _assert_frames(image, data)

        # out parameter doesn't work as expected
        out = numpy.zeros((531, 532, 3), numpy.uint8)
        data = lif.images[1].asarray(out=out)
        assert data.shape == (531, 531, 3)
        assert data.sum(dtype=numpy.uint64) == 676414

        out = numpy.zeros((531, 531, 3), numpy.uint8)
        with pytest.raises(ValueError):
            lif.images[1].asarray(out=out)


def test_channel_names_multiband():
    """Test channel names from MultiBand in ATLConfocalSettingDefinition."""
    filename = DATA / 'Experiment001.lif'
    with LifFile(filename) as lif:
        image = lif.images[0]
        assert image.sizes == {'C': 2, 'Y': 512, 'X': 512}
        # names come from MultiBand in main ATLConfocalSettingDefinition,
        # with 'Leica/' prefix stripped
        assert_array_equal(image.coords['C'], ['EGFP', 'dTomato'])


def test_channel_names_sequential():
    """Test channel names from MultiBand in sequential scan steps."""
    filename = DATA / 'Raw Stacks.lif'
    with LifFile(filename) as lif:
        image = lif.images[0]
        assert image.name == 'Series038'
        assert image.sizes == {'Z': 87, 'C': 3, 'Y': 256, 'X': 256}
        # names come from per-step MultiBand in LDM_Block_Sequential,
        # with 'Leica/' prefix stripped
        assert_array_equal(image.coords['C'], ['ECFP', 'EYFP', 'mCherry'])


def test_issue_memoryblocks():
    """Test reading sequence of LifMemoryBlocks."""
    # this file failed with Liffile < 2026.1.22
    filename = DATA / 'image.sc_107410/Edu_examples.lif'
    with LifFile(filename) as lif:
        assert len(lif.images) == 1
        assert len(lif.memory_blocks) == 2
        assert len(lif.children) == 0

        image = lif.images[0]
        assert image.dtype == numpy.uint8
        assert image.sizes == {'C': 4, 'Z': 10, 'Y': 1024, 'X': 1024}
        data = image.asxarray()
        assert data.shape == (4, 10, 1024, 1024)

        _assert_frames(image, data.values)

        memblock = lif.memory_blocks['MemBlock_102']
        assert memblock.offset == 195097
        assert memblock.size == 41943040

        memblock = lif.memory_blocks['MemBlock_95']
        assert memblock.offset == 195051
        assert memblock.size == 0


@pytest.mark.parametrize('asxarray', [False, True])
@pytest.mark.parametrize(
    'output', ['ndarray', 'memmap', 'memmap:.', 'filename']
)
def test_output(output, asxarray):
    """Test out parameter, including memmap."""
    filename = DATA / 'zenodo_3382102/y293-Gal4_vmat-GFP-f01.lif'

    if output == 'ndarray':
        out = numpy.zeros((86, 2, 500, 616), numpy.uint16)
    elif output == 'filename':
        out = tempfile.TemporaryFile()  # noqa: SIM115
    elif output == 'memmap:.':
        out = output
    else:
        out = 'memmap'

    im = imread(filename, asxarray=asxarray, out=out)

    if output == 'ndarray':
        im = out
        assert not isinstance(im, numpy.memmap)
    elif asxarray:
        assert isinstance(im.data, numpy.memmap), type(im.data)
    else:
        assert isinstance(im, numpy.memmap)
    assert im[:, 1, 200, 300].sum(axis=0) == 1364
    if output == 'filename':
        out.close()


def test_lof_no_image():
    """Test LOF file with no image."""
    filename = (
        DATA
        / 'XLEFReaderForBioformats/falcon_sample_data_small'
        / 'XLEF-LOF falcon_sample_data_small/Series003'
        / 'FrameProperties.lof'
    )
    with LifFile(filename) as lof:
        str(lof)
        assert lof.type == LifFileType.LOF
        assert len(lof.images) == 0
        memblock = lof.memory_blocks['MemBlock_1642']
        assert len(memblock.read()) == memblock.size


def test_lof_oldstyle(caplog):
    """Test LOF file without LMSDataContainerHeader XML elementL."""
    # the file is formally tested in test_xlif
    filename = (
        DATA
        / 'Leica_Image_File_Format Examples_2015_08'
        / '2015_03_16_14_16_18--Proj_LOF001'
        / 'ImageXYC1.lof'
    )
    with LifFile(filename) as lof:
        assert 'Element element not found in XML' not in caplog.text
        str(lof)
        assert lof.version == 2
        assert len(lof.images) == 1
        assert lof.memory_blocks['MemBlock_0'].offset == 62
        assert lof.xml_header().startswith('<Data>')
        image = lof.images[0]
        assert image.name == 'ImageXYC1'
        assert image.uuid is None


def test_phasor_from_lif():
    """Test PhasorPy phasor_from_lif function."""
    from phasorpy.io import phasor_from_lif

    filename = DATA / 'FLIM_testdata/FLIM_testdata.lif'
    mean, real, imag, attrs = phasor_from_lif(filename)
    for data in (mean, real, imag):
        assert data.shape == (1024, 1024)
        assert data.dtype == numpy.float32
    assert attrs['frequency'] == 19.505
    assert 'harmonic' not in attrs

    # select series
    mean1, _real1, _imag1, attrs = phasor_from_lif(
        filename, image='FLIM Compressed'
    )
    assert_array_equal(mean1, mean)

    # TODO: file does not contain FLIM raw metadata
    # filename = private_file('....lif')
    # mean, real, imag, attrs = phasor_from_lif(filename)
    # assert 'frequency' not in attrs

    # file does not contain FLIM data
    filename = DATA / 'ScanModesExamples.lif'
    with pytest.raises(ValueError):
        phasor_from_lif(filename)


def test_signal_from_lif(scanmodes_file):
    """Test PhasorPy signal_from_lif function."""
    from phasorpy.io import signal_from_lif

    signal = signal_from_lif(scanmodes_file)
    assert signal.dims == ('C', 'Y', 'X')
    assert signal.shape == (9, 128, 128)
    assert signal.dtype == numpy.uint8
    assert_allclose(signal.coords['C'].data[[0, 1]], [560.0, 580.0])

    # select series
    signal = signal_from_lif(scanmodes_file, image='XYZLambdaT')
    assert signal.dims == ('T', 'C', 'Z', 'Y', 'X')
    assert signal.shape == (7, 9, 5, 128, 128)
    assert_allclose(signal.coords['C'].data[[0, 1]], [560.0, 580.0])
    assert_allclose(signal.coords['T'].data[[0, 1]], [0.0, 23.897167])
    assert_allclose(
        signal.coords['Z'].data[[0, 1]], [4.999881e-6, 2.499821e-6]
    )

    # select excitation
    signal = signal_from_lif(scanmodes_file, dim='Λ')
    assert signal.dims == ('C', 'Y', 'X')
    assert signal.shape == (10, 128, 128)
    assert_allclose(signal.coords['C'].data[[0, 1]], [470.0, 492.0])

    # series does not contain dim
    with pytest.raises(ValueError):
        signal_from_lif(scanmodes_file, image='XYZLambdaT', dim='Λ')

    # file does not contain hyperspectral signal
    filename = DATA / 'FLIM_testdata/FLIM_testdata.lif'
    with pytest.raises(ValueError):
        signal_from_lif(filename)


@pytest.mark.parametrize('path', ['FLIM', 'flim'])
@pytest.mark.parametrize('name', ['FLIM', 'flim'])
def test_case_sensitive_path(path, name):
    """Test case_sensitive_path function."""
    assert case_sensitive_path(
        str(DATA / f'case_sensitive/{path}_testdata/{name}_testdata.xlef')
    ) == str(DATA / 'case_sensitive/FLIM_testdata/FLIM_testdata.xlef')


def test_xml2dict():
    """Test xml2dict function."""
    xml = ElementTree.fromstring("""<?xml version="1.0" ?>
    <root attr="attribute">
        <int>-1</int>
        <ints>-1,2</ints>
        <float>-3.14</float>
        <floats>1.0, -2.0</floats>
        <bool>True</bool>
        <string>Lorem, Ipsum</string>
    </root>
    """)
    d = xml2dict(xml)['root']
    assert d['attr'] == 'attribute'
    assert d['int'] == -1
    assert d['ints'] == (-1, 2)
    assert d['float'] == -3.14
    assert d['floats'] == (1.0, -2.0)
    assert d['bool'] is True
    assert d['string'] == 'Lorem, Ipsum'

    d = xml2dict(xml, prefix=('a_', 'b_'), sep='')['root']
    assert d['ints'] == '-1,2'
    assert d['floats'] == '1.0, -2.0'


@pytest.mark.skipif(
    not hasattr(sys, '_is_gil_enabled'), reason='Python < 3.12'
)
def test_gil_enabled():
    """Test that GIL is disabled on thread-free Python."""
    assert sys._is_gil_enabled() != sysconfig.get_config_var('Py_GIL_DISABLED')


@pytest.mark.parametrize(
    'filename',
    itertools.chain.from_iterable(
        glob.glob(f'**/*{ext}', root_dir=DATA, recursive=True)
        for ext in FILE_EXTENSIONS
    ),
)
def test_glob(filename):
    """Test read all LIF files."""
    if 'defective' in filename:
        pytest.xfail(reason='file is marked defective')
    filename = DATA / filename
    with LifFile(filename) as lif:
        str(lif)
        if lif.type == LifFileType.LIFEXT:
            assert len(lif.images) > 0
        elif lif.name in {
            'FrameProperties',
            'IOManagerConfiguation',  # typo
            '',
        }:
            assert len(lif.images) == 0
        elif lif.type == LifFileType.LOF:
            assert len(lif.images) == 1
        else:
            assert len(lif.images) > 0
        for image in lif.images:
            str(image)
            if image.is_flim:
                with pytest.raises(NotImplementedError):
                    image.asxarray()
            else:
                image.asxarray()
            _ = image.timestamps
            for ax in 'QA?':
                if ax in image.dims:
                    msg = f'unexpected dimension {ax!r} in file {filename!r}'
                    raise ValueError(msg)


if __name__ == '__main__':
    import warnings

    # warnings.simplefilter('always')
    warnings.filterwarnings('ignore', category=ImportWarning)
    argv = sys.argv
    argv.append('--cov-report=html')
    argv.append('--cov=liffile')
    argv.append('--verbose')
    sys.exit(pytest.main(argv))

# mypy: allow-untyped-defs
# mypy: check-untyped-defs=False
