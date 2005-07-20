########################################################################
#
# File:   gcc_test_base.py
# Author: Mark Mitchell
# Date:   05/15/2003
#
# Contents:
#   GCCTestBase
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   compiler import Compiler, GCC
from   dejagnu_test import DejaGNUTest
from   dg_test import DGTest
import os
import re

########################################################################
# Classes
########################################################################

class GCCTestBase:
    """A 'GCCTestBase' is a base for all GCC tests.

    This class emulates functionality in 'gcc-defs.exp' in the GCC
    testsuite."""

    KIND_PREPROCESS = "preprocess"
    KIND_COMPILE = "assembly"
    KIND_ASSEMBLE = "object"
    KIND_EXECUTABLE = "executable"
    KIND_PRECOMPILE = "precompiled_header"
    
    _test_kind_map = {
        DGTest.KIND_PREPROCESS : KIND_PREPROCESS,
        DGTest.KIND_COMPILE : KIND_COMPILE,
        DGTest.KIND_ASSEMBLE : KIND_ASSEMBLE,
        DGTest.KIND_LINK : KIND_EXECUTABLE,
        DGTest.KIND_RUN : KIND_EXECUTABLE,
        KIND_PRECOMPILE : KIND_PRECOMPILE
        }
    """A map from dg-do keywords to compilation kinds."""

    __signal_regexp \
          = re.compile(".*cc: Internal compiler error: program.*got fatal "
                       "signal (6|11)")
    """A regular expression matching the output from a fatal signal."""

    __newline_regexp = re.compile(r"[\r\n]")
    """A regular expression matching newline characters."""

    _language = "c"
    """The name of the programming language being compiled.

    This value should correspond to the one of the entries in the
    'CompilerTable'."""

    _options_context_property = None
    """The name of the context property containing extra options.

    If not 'None', the context contains a property with this name, and
    the corresponding value is a list of options that should be
    provided to every test."""

    _libdir_context_property = None
    """The name of the context property containing library directories.

    If not 'None', the context contains a property with this name, and
    the corresponding value is a list of directories that should be
    searched for libraries."""
    
    __compilation_mode_map = {
        KIND_PREPROCESS : Compiler.MODE_PREPROCESS,
        KIND_COMPILE : Compiler.MODE_COMPILE,
        KIND_ASSEMBLE : Compiler.MODE_ASSEMBLE,
        KIND_EXECUTABLE : Compiler.MODE_LINK,
        KIND_PRECOMPILE : GCC.MODE_PRECOMPILE,
        }
    """A map from DejaGNU compilation modes to 'Compiler' modes."""

    def _RecordPass(self, result, testcase, cflags):
        """Emulate '${tool}_pass'.

        'result' -- The 'Result'.
        
        'testcase' -- The name of the test.

        'cflags' -- The options provided to the test."""

        if cflags:
            message = "%s, %s" % (testcase, cflags)
        else:
            message = testcase
        self._RecordDejaGNUOutcome(result, DejaGNUTest.PASS, message)


    def _RecordFail(self, result, testcase, cflags):
        """Emulate '${tool}_fail'.

        'result' -- The 'Result'.
        
        'testcase' -- The name of the test.

        'cflags' -- The options provided to the test."""

        if cflags:
            message = "%s, %s" % (testcase, cflags)
        else:
            message = testcase
        self._RecordDejaGNUOutcome(result, DejaGNUTest.FAIL, message)


    def _Compile(self, context, result, source_files, output_file, mode,
                 options = [], post_options = []):
        """Compile the 'source_files'.

        'context' -- The 'Context' in which the test is running.
        
        'result' -- The QMTest 'Result' for the test or resource.
        
        'source_files' -- A list of paths giving the source files to be
        compiled.

        'output_file' -- The name of the output file to be created.

        'mode' -- One of the DejaGNU compilation modes.

        'options' -- A list of additional command-line options to be
        provided to the compiler.

        returns -- The output produced by the compiler."""

        # This method emulates gcc_target_compile (in the GCC
        # testsuite), and target_compile (in the DejaGNU
        # distribution).

        # There are a lot of complexities in default_target_compile
        # which we do not presently attempt to emulate.
        # Form the command-line.  Using Compiler.GetCompilationCommand
        # isn't guaranteed to create exactly the same command used by
        # DejaGNU, so we form the command manually.
        compiler = context["CompilerTable.compilers"][self._language]
        command = [compiler.GetPath()]
        # Add the global options (as originally specified in the
        # context file).  These are added before the options for this
        # test so that the latter can override the former.
        if self._options_context_property is not None:
            command += context[self._options_context_property]
        else:
            command += compiler.GetOptions()
        command += options
        # Add the source files.
        mode = self.__compilation_mode_map[mode]
        if mode != Compiler.MODE_ASSEMBLE:
            command += source_files
        # Indicate the compilation mode.
        command += compiler._GetModeSwitches(mode)
        # For an executable test, provide necessary -L options.
        if (mode == Compiler.MODE_LINK
            and self._libdir_context_property is not None):
            command += map(lambda d: "-L" + d,
                           context[self._libdir_context_property])
        # Indicate where the output should go.
        command += ["-o", output_file]
        # Add the source files if they have not already been added.
        if mode == Compiler.MODE_ASSEMBLE:
            command += source_files
        elif mode == Compiler.MODE_LINK:
            command += compiler.GetLDFlags()

        # Run the compiler.
        index = self._RecordCommand(result, command)
        status, output \
           = compiler.ExecuteCommand(context.GetTemporaryDirectory(), command)
        self._RecordCommandOutput(result, index, status, output)
                    
        # If there was no output, DejaGNU uses the exit status.
        if not output and status != 0:
            output = "exit status is %d" % status

        return output
        
        
    def _CheckCompile(self, result, testcase, option, objname, gcc_output):
        """Check the result of a compilation.

        'result' -- The QMTest 'Result' object.
        
        'testcase' -- The name of the test.

        'option' -- The options used when performing the test.

        'objname' -- The name of the output file.

        'gcc_output' -- The output generated by the compiler.

        returns -- '1' if the compilation suceeded, '0' otherwise.  If
        '0' is returned, the 'result' has been updated to indicate the
        problem.
        
        This function emulates 'g++_check_compile' in
        'gcc-defs.exp'."""

        match = GCCTestBase.__signal_regexp.match(gcc_output)
        if match:
            self._RecordFail(result, testcase,
                             "Got Signal %s, %s" % (match.group(1), option))
            return 0

        gcc_output = GCCTestBase.__newline_regexp.sub(gcc_output, "")
                
        if gcc_output != "":
            self._RecordFail(result, testcase, option)
            return 0
            
        if objname and not os.path.exists(objname):
            self._RecordFail(result, testcase, option)
            return 0
        
        self._RecordPass(result, testcase, option)
        return 1

        
    
