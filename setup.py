from setuptools import setup, find_packages

version = '0.0.0'
install_requires = [
    'pyqt5',
    'matplotlib',
]

setup(name='chainer_wind',
      version=version,
      description='Flowchart Python -- A multipurpose Python node editor.',
      keywords='Flowchart',
      author='fukatani',
      license="BSD 3-Clause",
      packages=find_packages(),
      package_data={'floppy': ['resources/*', ], },
      install_requires=install_requires,
      )
