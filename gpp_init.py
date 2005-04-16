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
from   qm.test.result import Result
import os
import sys

########################################################################
# Classes
########################################################################

class GPPInit(Resource, DejaGNUBase):
    """A 'GPPInit' resource stores information for G++ tests.

    Every C++ test depends on a 'GPPInit' resource."""

    def SetUp(self, context, result):

        super(GPPInit, self)._SetUp(context)
        
        # Find the compiler table.
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

        # Assume that no additional library directories need to be
        # explicitly provided to the compiler. 
        context["GPPInit.library_directories"] = []
        
        # If the compiler is being run out of the build directory,
        # perform special set up associated with that configuration.
        # To determine whether the compiler is being run out of the
        # build directory, we find the compiler by looking for the
        # first -B option.  (This is the technique used by
        # get_multilibs in libgloss.exp.)
        for o in options:
            if o.startswith("-B"):
                objdir = os.path.dirname(os.path.dirname(o[2:]))
                options.append(self.__SetUpInObjdir(result, context, objdir))
                break
        

        # Avoid splitting diagnostic message lines.
        options.append("-fmessage-length=0")
        # Remember the options to use.
        context["GPPInit.options"] = options
        

    def __SetUpInObjdir(self, result, context, objdir):
        """Setup for a compiler being run out of the build directory.

        'objdir' -- The path to the 'objdir' directory, i.e., the
        directory that contains 'xgcc'.
        
        'result' -- As for 'SetUp'.

        'context' -- As for 'SetUp'.

        returns -- A list of additional command-line options that
        should be provided to the compiler.
        
        It the compiler being tested is not an installed compiler, but
        is in in the GCC build directory, then additional command-line
        options must be passed to 'g++' to make it aware of the
        location of various components."""

        # Compute the path to the V3 object directory.  See 'g++_init'
        # in the GCC testsuite for the DejaGNU equivalent to this
        # code.
        target = context["DejaGNUTest.target"]
        v3_directory = os.path.normpath(os.path.join(objdir,
                                                     target,
                                                     directory,
                                                     "libstdc++-v3"))

        # Run "testsuite_flags" to figure out which -I options to use
        # when running tests.
        command = [os.path.join(v3_directory,
                                "scripts",
                                "testsuite_flags"),
                   "--build-includes"]
        result["GPPInit.testsuite_flags_command"] \
            = result.Quote(" ".join(command))
        try:
            executable = RedirectedExecutable()
            executable.Run(command)
            options = executable.stdout.split()
        except:
            result.NoteException(cause="Could not run testsuite_flags",
                                 outcome=Result.FAIL)
            return []

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
    
        return options
