import os
from setuptools import setup, find_packages


with open(
    os.path.join(os.path.dirname(__file__), 'README.md'),
    encoding='utf-8'
) as fh:
    long_description = fh.read()


setup(name='damn-simple-jsonrpc-server',
      version='0.4.4.post1',
      description='Damn simple, framework-agnostic JSON-RPC server',
      classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      author='Marcin Nowak',
      author_email='marcin.j.nowak@gmail.com',
      url='https://github.com/marcinn/json-rpc-server',
      keywords='web json rpc python server',
      long_description=long_description,
      long_description_content_type='text/markdown',
      packages=find_packages('.'),
      include_package_data=True,
      zip_safe=False,
      )
