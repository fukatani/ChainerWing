from setuptools import setup, find_packages

version = '0.1.0'
install_requires = [
    'pyqt5',
    'matplotlib',
]

setup(name='chainer_wing',
      version=version,
      description='ChainerWing -- GUI Deep Learning IDE.',
      keywords='Deep Learning',
      author='fukatani',
      license="BSD 3-Clause",
      packages=find_packages(),
      package_data={'chainer_wing': ['resources/*', ], },
      install_requires=install_requires,
      )
