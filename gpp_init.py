########################################################################
#
# File:   gpp_init.py
# Author: Mark Mitchell
# Date:   04/19/2003
#
# Contents:
#   GPPInit
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   compiler import CompilerExecutable
from   compiler_table import CompilerTable
from   dejagnu_base import DejaGNUBase
from   qm.executable import RedirectedExecutable
from   qm.test.resource import Resource
import os

########################################################################
# Classes
########################################################################

class GPPInit(Resource, DejaGNUBase):
    """A 'GPPInit' resource stores information for G++ tests.

    Every test in the database depends on a 'DejaGNUCompilerTable'
    resource."""

    def SetUp(self, context, result):

        super(GPPInit, self)._SetUp(context)
        
        # Find the ordinary compiler table.
        compilers = context["CompilerTable.compiler_table"]

        # Get the C++ compiler.
        compiler = compilers["cplusplus"]

        # Tell GCOVTest where the coverage executable is located.
        gcov = os.path.join(os.path.dirname(compiler.GetPath()),
                            "gcov")
        context["GCOVTest.gcov"] = gcov
        
        # Run the compiler to find out what multilib directory is
        # in use. The DejaGNU code that does this is get_multiblis in
        # libgloss.exp; this version uses a much simpler technique.
        options = compiler.GetOptions()
        executable = CompilerExecutable()
        executable.Run([compiler.GetPath()]
                       + options
                       + ['--print-multi-dir'])
        directory = executable.stdout[:-1]
        
        # Find the directory containing the compiler by looking for
        # the first -B option.  (This is the technique used by
        # get_multilibs in libgloss.exp.)
        for o in options:
            if o.startswith("-B"):
                objdir = os.path.dirname(os.path.dirname(o[2:]))
                break
        
        # Compute the path to the V3 object directory.  See 'g++_init'
        # in the GCC testsuite for the DejaGNU equivalent to this
        # code.
        target = context["DejaGNUTest.target"]
        v3_directory = os.path.normpath(os.path.join(objdir,
                                                     target,
                                                     directory,
                                                     "libstdc++-v3"))

        # Add -I flags so that the tests can find the V3 headers.
        executable = RedirectedExecutable()
        executable.Run([os.path.join(v3_directory, "testsuite_flags"),
                        "--build-includes"])
        options += executable.stdout.split()
        # Avoid splitting diagnostic message lines.
        options.append("-fmessage-length=0")
        # Remember the options to use.
        context["GPPInit.options"] = options

        # Compute the directories containing runtime libraries.  These
        # directories must be provided both at link-time (in the form
        # of -L options) and at run-time (in LD_LIBRARY_PATH).
        lib_dirs = []
        lib_dirs.append(os.path.join(v3_directory, "src", ".libs"))
        lib_dirs.append(os.path.join(objdir, "gcc"))
        context["GPPInit.library_directories"] = lib_dirs
    

