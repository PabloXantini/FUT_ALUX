from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import sys

class get_pybind_include(object):
    def __init__(self, user=False):
        self.user = user

    def __str__(self):
        import pybind11
        return pybind11.get_include(self.user)

ext_modules = [
    Extension(
        'fast_math',
        ['fast_math.cpp'],
        include_dirs=[
            get_pybind_include(),
            get_pybind_include(user=True)
        ],
        language='c++'
    ),
]

setup(
    name='fast_math',
    version='0.0.1',
    author='PabloXantini',
    description='Fast 3D Projection using pybind11',
    ext_modules=ext_modules,
    setup_requires=['pybind11>=2.5.0'],
    zip_safe=False,
)
