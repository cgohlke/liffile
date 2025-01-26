# test_liffile.py

# Copyright (c) 2023-2025, Christoph Gohlke
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

# mypy: allow-untyped-defs
# mypy: check-untyped-defs=False

"""Unittests for the liffile package.

:Version: 2025.1.26

"""

import datetime
import glob
import io
import os
import pathlib
import re
import sys
import tempfile
from xml.etree import ElementTree

import liffile
import numpy
import pytest
import xarray
from liffile import (
    FILE_EXTENSIONS,
    LifFile,
    LifFileError,
    LifImage,
    LifImageSeries,
    LifMemoryBlock,
    __version__,
    imread,
    logger,
)
from numpy.testing import assert_allclose, assert_array_equal
from xarray import DataArray

HERE = pathlib.Path(os.path.dirname(__file__))
DATA = HERE / 'data'

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
    ('XYLamdaZ', {'Z': 5, 'λ': 9, 'Y': 128, 'X': 128}, 'uint8'),
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
    (
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


@pytest.mark.skipif(__doc__ is None, reason='__doc__ is None')
def test_version():
    """Assert liffile versions match docstrings."""
    ver = ':Version: ' + __version__
    assert ver in __doc__
    assert ver in liffile.__doc__


def test_not_lif():
    """Test open non-LIF file raises LifFileError."""
    with pytest.raises(LifFileError):
        imread(DATA / 'empty.bin')
    with pytest.raises(LifFileError):
        imread(DATA / 'ScanModesExamples.lif.xml')


@pytest.mark.parametrize('asxarray', [False, True])
def test_imread(asxarray):
    """Test imread function."""
    filename = DATA / 'ScanModesExamples.lif'

    data = imread(filename, series=5, asrgb=True, out=None, asxarray=asxarray)
    if asxarray:
        assert isinstance(data, DataArray)
        assert data.sizes == {'T': 7, 'Z': 5, 'C': 2, 'Y': 128, 'X': 128}
        data = data.data
    else:
        assert isinstance(data, numpy.ndarray)
    assert data.shape == (7, 5, 2, 128, 128)
    assert data.sum(dtype=numpy.uint32) == 27141756


@pytest.mark.parametrize('filetype', [str, io.BytesIO])
def test_liffile(filetype):
    """Test LifFile API."""
    filename = DATA / 'ScanModesExamples.lif'
    file = filename if filetype is str else open(filename, 'rb')

    with LifFile(file, mode='r+b', squeeze=True) as lif:
        str(lif)
        if filetype is str:
            assert lif.filename == str(filename)
        else:
            assert lif.filename == ''
        assert lif.name == 'ScanModiBeispiele.lif'
        assert lif.version == 2
        assert lif.datetime == datetime.datetime(
            2013, 12, 2, 8, 27, 44, tzinfo=datetime.timezone.utc
        )
        assert lif.flim_rawdata == {}
        assert len(lif.memory_blocks) == 240
        assert isinstance(lif.xml_header, str)
        assert isinstance(lif.xml_element, ElementTree.Element)

        series = lif.series
        str(series)
        assert isinstance(series, LifImageSeries)
        assert len(series) == 200

        for path, im in zip(series.paths(), series):
            assert im.path == path
            assert isinstance(im, LifImage)

        images = series.findall('XZEXcLambda/Lambda.*', flags=re.IGNORECASE)
        assert len(images) == 9
        assert images[0].name == 'Lambda_496nm'

        im = series[5]
        str(im)
        assert series[im.path] is im
        assert series[im.name + '$'] is im
        assert im.parent == lif
        assert im.name == 'XYZT'
        assert im.path == 'XYZT'
        assert im.dtype == numpy.uint8
        assert im.itemsize == 1
        assert im.shape == (7, 5, 2, 128, 128)
        assert im.dims == ('T', 'Z', 'C', 'Y', 'X')
        assert im.sizes == {'T': 7, 'Z': 5, 'C': 2, 'Y': 128, 'X': 128}
        assert 'C' not in im.coords
        assert_allclose(im.coords['T'][[0, -1]], [0.0, 10.657])
        assert_allclose(im.coords['Z'][[0, -1]], [4.999881e-06, -5.000359e-06])
        assert_allclose(im.coords['Y'][[0, -1]], [-3.418137e-05, 3.658182e-04])
        assert_allclose(im.coords['X'][[0, -1]], [8.673617e-20, 3.999996e-04])
        assert im.attrs['path'] == im.parent.name + '/' + im.path
        assert len(im.timestamps) == 70
        assert im.timestamps[0] == numpy.datetime64('2013-12-02T09:49:26.347')
        assert im.size == 1146880
        assert im.nbytes == 1146880
        assert im.ndim == 5
        assert isinstance(im.xml_element, ElementTree.Element)

        with pytest.raises(NotImplementedError):
            for frame in im.frames():
                pass

        attrs = im.attrs['HardwareSetting']
        assert attrs['Software'] == 'LAS-AF [ BETA ] 3.3.0.10067'
        assert attrs['ATLConfocalSettingDefinition']['LineTime'] == 0.0025

        data = im.asarray(asrgb=False, mode='r', out=None)
        assert isinstance(data, numpy.ndarray)
        xdata = im.asxarray(asrgb=False, mode='r', out=None)
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
        assert memory_block.read(lif.filehandle) == data.tobytes()

    if filetype is not str:
        file.close()
    else:
        with pytest.raises(ValueError):
            lif = LifFile(file, mode='abc')


@pytest.mark.parametrize('index', range(len(SCANMODES)))
def test_scan_modes(index):
    """Test scan modes."""
    filename = DATA / 'ScanModesExamples.lif'
    path, sizes, dtype = SCANMODES[index]
    shape = tuple(sizes.values())
    with LifFile(filename, squeeze=False) as lif:
        image = lif.series[index]
        assert image.path == path
        assert image.sizes == sizes
        assert image.shape == shape
        assert image.dtype == dtype
        assert image.timestamps is not None
        data = image.asxarray()
        assert data.shape == shape
        assert data.dtype == dtype

    if 1 in sizes.values():
        sizes = {k: v for k, v in sizes.items() if v > 1}
        shape = tuple(sizes.values())
        with LifFile(filename) as lif:
            image = lif.series[index]
            assert image.path == path
            assert image.sizes == sizes
            assert image.shape == shape
            assert image.dtype == dtype
            data = image.asxarray()
            assert data.shape == shape
            assert data.dtype == dtype


def test_flim():
    """Test read FLIM dataset."""
    filename = DATA / 'FLIM_testdata/FLIM_testdata.lif'
    with LifFile(filename) as lif:
        flim = lif.flim_rawdata
        assert flim['LaserPulseFrequency'] == 19505000

        intensity = lif.series['/Intensity']
        data = intensity.asxarray()
        assert data.shape == (1024, 1024)
        assert data.dtype == numpy.float32
        assert data.attrs['TileScanInfo']['Tile']['PosX'] == -0.0471300149

        mean = lif.series['Phasor Intensity$']
        data = mean.asxarray()
        assert data.shape == (1024, 1024)
        assert data.dtype == numpy.float16
        assert data.attrs['TileScanInfo']['Tile']['PosX'] == -0.0471300149

        real = lif.series['Phasor Real']
        data = real.asxarray()
        assert data.shape == (1024, 1024)
        assert data.dtype == numpy.float16
        assert data.attrs['F16']['FactorF32ToF16'] == 1.0

        real = lif.series['Fast Flim']
        data = real.asxarray()
        assert data.shape == (1024, 1024)
        assert data.dtype == numpy.float16
        assert data.attrs['F16']['FactorF32ToF16'] == 1000000000.0

        mask = lif.series['Phasor Mask']
        data = mask.asxarray()
        assert data.shape == (1024, 1024)
        assert data.dtype == numpy.uint32
        gamma = data.attrs['ViewerScaling']['ChannelScalingInfo']['GammaValue']
        assert gamma == 1.0


def test_rgb():
    """Test read 6 channel RGB."""
    filename = DATA / 'RGB/Experiment.lif'
    with LifFile(filename) as lif:
        image = lif.series[0]
        assert image.sizes == {'C': 2, 'Y': 1536, 'X': 2048, 'S': 3}
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

        data = image.asxarray(asrgb=False)
        assert_array_equal(
            data.sum(dtype=numpy.uint64, axis=(0, 1, 2)),
            [82284132, 9225469, 12387812],
        )

        image = lif.series[1]
        assert image.sizes == {'Y': 1536, 'X': 2048, 'S': 3}
        data = image.asarray()
        assert data.sum(dtype=numpy.uint64) == 86724120


@pytest.mark.parametrize('asxarray', [False, True])
@pytest.mark.parametrize('output', ['ndarray', 'memmap', 'memmap:.', 'fname'])
def test_output(output, asxarray):
    """Test out parameter, including memmap."""
    filename = DATA / 'zenodo_3382102/y293-Gal4_vmat-GFP-f01.lif'

    if output == 'ndarray':
        out = numpy.zeros((86, 2, 500, 616), numpy.uint16)
    elif output == 'fname':
        out = tempfile.TemporaryFile()
    elif output == 'memmap:.':
        out = output
    else:
        out = 'memmap'

    im = imread(filename, asxarray=asxarray, out=out)

    if output == 'ndarray':
        im = out
        assert not isinstance(im, numpy.memmap)
    elif asxarray:
        assert isinstance(im.data, numpy.memmap)
    else:
        assert isinstance(im, numpy.memmap)
    assert im[:, 1, 200, 300].sum(axis=0) == 1364
    if output == 'fname':
        out.close()


@pytest.mark.parametrize(
    'fname', glob.glob('**/*.lif', root_dir=DATA, recursive=True)
)
def test_glob(fname):
    """Test read all LIF files."""
    if 'defective' in fname:
        pytest.xfail(reason='file is marked defective')
    fname = DATA / fname
    with LifFile(fname) as lif:
        str(lif)
        for image in lif.series:
            str(image)
            image.asxarray()
            image.timestamps


if __name__ == '__main__':
    import warnings

    # warnings.simplefilter('always')
    warnings.filterwarnings('ignore', category=ImportWarning)
    argv = sys.argv
    argv.append('--cov-report=html')
    argv.append('--cov=liffile')
    argv.append('--verbose')
    sys.exit(pytest.main(argv))
