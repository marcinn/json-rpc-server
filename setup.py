from setuptools import setup, find_packages

setup(name='damn-simple-jsonrpc-server',
      version='0.4.3',
      description='Damn simple, framework-agnostic JSON-RPC server',
      classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 2.7",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      author='Marcin Nowak',
      author_email='marcin.j.nowak@gmail.com',
      url='https://github.com/marcinn/json-rpc-server',
      keywords='web json rpc python server',
      packages=find_packages('.'),
      include_package_data=True,
      zip_safe=False,
      )
