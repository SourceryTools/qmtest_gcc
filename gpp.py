########################################################################
#
# File:   gpp.py
# Author: Mark Mitchell
# Date:   04/21/2003
#
# Contents:
#   Routines shared by G++ tests and resources.
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   compiler import Compiler, GPP
import os

########################################################################
# Variables
########################################################################

KIND_PREPROCESS = "preprocess"
KIND_COMPILE = "assembly"
KIND_ASSEMBLE = "object"
KIND_EXECUTABLE = "executable"
KIND_PRECOMPILE = "precompiled_header"

__compilation_mode_map = {
    KIND_PREPROCESS : Compiler.MODE_PREPROCESS,
    KIND_COMPILE : Compiler.MODE_COMPILE,
    KIND_ASSEMBLE : Compiler.MODE_ASSEMBLE,
    KIND_EXECUTABLE : Compiler.MODE_LINK,
    KIND_PRECOMPILE : GPP.MODE_PRECOMPILE,
    }
"""A map from DejaGNU compilation modes to 'Compiler' modes."""

########################################################################
# Functions
########################################################################

def compile(context, result, source_files, output_file, mode,
            options = [], test = None):
        """Compile the 'source_files'.

        'context' -- The 'Context' in which the test is running.
        
        'result' -- The QMTest 'Result' for the test or resource.
        
        'source_files' -- A list of paths giving the source files to be
        compiled.

        'output_file' -- The name of the output file to be created.

        'mode' -- One of the DejaGNU compilation modes.

        'options' -- A list of additional command-line options to be
        provided to the compiler.

        'test' -- The 'Test' object which is running, or 'None'.

        returns -- The output produced by the compiler."""

        # This method emulates g++_target_compile (in the GCC
        # testsuite), and target_compile (in the DejaGNU distribution).

        # There are a lot of complexities in default_target_compile
        # which we do not presently attempt to emulate.
        # Form the command-line.  Using Compiler.GetCompilationCommand
        # isn't guaranteed to create exactly the same command used by
        # DejaGNU, so we form the command manually.
        compiler = context["CompilerTable.compiler_table"]["cplusplus"]
        command = [compiler.GetPath()]
        # Add the global options (as originally specified in the
        # context file).  These are added before the options for this
        # test so that the latter can override the former.
        command += context["GPPInit.options"]
        command += options
        # Add the source files.
        mode = __compilation_mode_map[mode]
        if mode != Compiler.MODE_ASSEMBLE:
            command += source_files
        # Indicate the compilation mode.
        command += compiler._GetModeSwitches(mode)
        # For an executable test, provide necessary -L options.
        if mode == Compiler.MODE_LINK:
            command += map(lambda d: "-L" + d,
                           context["GPPInit.library_directories"])
        # Indicate where the output should go.
        command += ["-o", output_file]
        # Add the source files if they have not already been added.
        if mode == Compiler.MODE_ASSEMBLE:
            command += source_files

        # Run the compiler.
        if test:
            index = test._RecordCommand(result, command)
        status, output = compiler.ExecuteCommand(None, command)
        if test:
            test._RecordCommandOutput(result, index, status, output)
                    
        # If there was no output, DejaGNU uses the exit status.
        if not output and status != 0:
            output = "exit statis is %d" % status

        return output


def get_target_environment(context):
        """Return additional environment variables to set on the target.

        'context' -- The 'Context' in which this test is running.
        
        returns -- A map from strings (environment variable names) to
        strings (values for those variables).  These new variables are
        added to the environment when a program executes on the
        target."""
    
        env = {}
        dirs = ":".join(context["GPPInit.library_directories"])
        for v in ("LD_LIBRARY_PATH",
                  "SHLIB_PATH",
                  "LD_LIBRARY_N32_PATH",
                  "LD_LIBRARY64_PATH"):
            val = os.environ.get(v, "")
            if val:
                env[v] = val + ":" + dirs
            else:
                env[v] = dirs

        return env
        
        
