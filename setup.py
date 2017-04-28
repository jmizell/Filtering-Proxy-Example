from setuptools import setup

setup(name='filterproxy',
      version='0.1',
      description='sql filtering proxy server',
      author='Jeremy Mizell',
      author_email='jeremy.mizell@ottercove.net',
      packages=['filterproxy'],
      install_requires=[
            'Flask==0.12.1',
            'requests==2.13.0',
            'mock',
            'numpy==1.12.1',
            'SciPy==0.19.0',
            'scikit-learn==0.18.1'])
