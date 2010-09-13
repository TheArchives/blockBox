# Copyright (c) 2008 Twisted Matrix Laboratories.
# See LICENSE for details.
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
setup(name='iocpsupport',
      ext_modules=[Extension('iocpsupport',
                   ['iocpsupport/iocpsupport.pyx',
                    'iocpsupport/winsock_pointers.c'],
                   libraries = ['ws2_32'],
                   )
                  ],
      cmdclass = {'build_ext': build_ext},
      )

