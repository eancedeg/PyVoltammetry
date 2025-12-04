from setuptools import setup, find_packages

setup(
    name='PyVoltammetry',
    version='1.2',
    packages=find_packages(),
    install_requires=['pandas'],
    url='',
    license='GPL',
    author='Evys Ancede Gallardo',
    author_email='eancedeg@gmail.com',
    description='Package for parse Voltammogram files',
    python_requires='>=3.10',
)
