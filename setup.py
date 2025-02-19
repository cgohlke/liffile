# liffile/setup.py

"""Liffile package Setuptools script."""

import re
import sys

from setuptools import Extension, setup

buildnumber = ''


def search(pattern: str, string: str, flags: int = 0) -> str:
    """Return first match of pattern in string."""
    match = re.search(pattern, string, flags)
    if match is None:
        raise ValueError(f'{pattern!r} not found')
    return match.groups()[0]


def fix_docstring_examples(docstring: str) -> str:
    """Return docstring with examples fixed for GitHub."""
    start = True
    indent = False
    lines = ['..', '  This file is generated by setup.py', '']
    for line in docstring.splitlines():
        if not line.strip():
            start = True
            indent = False
        if line.startswith('>>> '):
            indent = True
            if start:
                lines.extend(['.. code-block:: python', ''])
                start = False
        lines.append(('    ' if indent else '') + line)
    return '\n'.join(lines)


with open('liffile/liffile.py', encoding='utf-8') as fh:
    code = fh.read()

version = search(r"__version__ = '(.*?)'", code).replace('.x.x', '.dev0')
version += ('.' + buildnumber) if buildnumber else ''

description = search(r'"""(.*)\.(?:\r\n|\r|\n)', code)

readme = search(
    r'(?:\r\n|\r|\n){2}"""(.*)"""(?:\r\n|\r|\n){2}from __future__',
    code,
    re.MULTILINE | re.DOTALL,
)
readme = '\n'.join(
    [description, '=' * len(description)] + readme.splitlines()[1:]
)

if 'sdist' in sys.argv:
    # update README and LICENSE files

    with open('README.rst', 'w', encoding='utf-8') as fh:
        fh.write(fix_docstring_examples(readme))

    license = search(
        r'(# Copyright.*?(?:\r\n|\r|\n))(?:\r\n|\r|\n)+""',
        code,
        re.MULTILINE | re.DOTALL,
    )
    license = license.replace('# ', '').replace('#', '')

    with open('LICENSE', 'w', encoding='utf-8') as fh:
        fh.write('BSD 3-Clause License\n\n')
        fh.write(license)

    revisions = search(
        r'(?:\r\n|\r|\n){2}(Revisions.*)- …',
        readme,
        re.MULTILINE | re.DOTALL,
    ).strip()

    with open('CHANGES.rst', encoding='utf-8') as fh:
        old = fh.read()

    old = old.split(revisions.splitlines()[-1])[-1]
    with open('CHANGES.rst', 'w', encoding='utf-8') as fh:
        fh.write(revisions.strip())
        fh.write(old)

ext_modules = [
    Extension(
        'liffile._liffile',
        ['liffile/_liffile.pyx'],
        define_macros=[
            # ('CYTHON_TRACE_NOGIL', '1'),
            # ('CYTHON_LIMITED_API', '1'),
            # ('Py_LIMITED_API', '1'),
            ('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION'),
        ],
    )
]

setup(
    name='liffile',
    version=version,
    license='BSD',
    description=description,
    long_description=readme,
    long_description_content_type='text/x-rst',
    author='Christoph Gohlke',
    author_email='cgohlke@cgohlke.com',
    url='https://www.cgohlke.com',
    project_urls={
        'Bug Tracker': 'https://github.com/cgohlke/liffile/issues',
        'Source Code': 'https://github.com/cgohlke/liffile',
        # 'Documentation': 'https://',
    },
    packages=['liffile'],
    package_data={'liffile': ['py.typed']},
    entry_points={'console_scripts': ['liffile = liffile.__main__:main']},
    python_requires='>=3.10',
    install_requires=['numpy'],
    extras_require={
        'all': ['xarray', 'tifffile', 'imagecodecs', 'matplotlib']
    },
    # ext_modules=ext_modules,
    zip_safe=False,
    platforms=['any'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
)
