########################################################################
#
# File:   setup.py
# Author: Mark Mitchell
# Date:   07/20/2005
#
# Contents:
#   Distutils setup script.
#
# Copyright (c) 2005 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from distutils.core import setup

########################################################################
# Main Program
########################################################################

setup(
    name = "qmtest_gcc",
    author = "CodeSourcery, LLC",
    author_email = "info@codesourcery.com",
    maintainer = "CodeSourcery, LLC",
    maintainer_email = "qmtest@codesourcery.com",
    description = "QMTest support for testing GCC",
    
    package_dir = { "qmtest_gcc" : "." },
    packages = ("qmtest_gcc",)
    )
      
      
      
