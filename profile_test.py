########################################################################
#
# File:   profile_test.py
# Author: Mark Mitchell
# Date:   04/21/2003
#
# Contents:
#   ProfileTest
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   dejagnu_test import DejaGNUTest
import glob
import os

########################################################################
# Classes
########################################################################

class ProfileTest(DejaGNUTest):
    """A 'ProfileTest' is a test using the 'profopt.exp' driver.

    This test class emulates the 'profile.exp' source file in the GCC
    testsuite."""

    options = (["-g",], ["-O0",], ["-O1",], ["-O2",], ["-O3",],
               ["-O3", "-g"], ["-Os",])
    """A list of optimization options.

    Each test is run with all of these options, in addition to the
    profiling options."""

    perf_ext = None
    """The performance file extension."""

    prof_ext = None
    """The profiling file extension."""

    feedback_option = None
    """The option to use to compile with profile-directed feedback."""
    
    profile_option = None
    """The option to use to compile with profiling."""
    
    def Run(self, context, result):

        # Initialize.
        self._SetUp(context)

        basename = os.path.basename(self.GetId())
        executable = os.path.join(self._GetTmpdir(),
                                  os.path.splitext(basename)[0] + ".x")
                      
        count = 0
        for options in self.options:
            execname1 = executable + str(count) + "1"
            execname2 = executable + str(count) + "2"
            execname3 = executable + str(count) + "3"
            count += 1

            try:
                os.remove(execname1)
                os.remove(execname2)
                os.remove(execname3)
            except:
                pass
            
            self.__CleanUp(self.prof_ext)
            if self.perf_ext:
                self.__CleanUp(self.perf_ext)

            o = options + [self.profile_option]
            ostr = " ".join(o)
            output = self._Compile(context, result,
                                   [self._GetSourcePath()],
                                   execname1,
                                   "executable",
                                   o)

            # Run the profiled executable.
            outcome = self._RunTargetExecutable(context, result, execname1)
            message = self.GetId() + " execution,   " + ostr
            if outcome == self.PASS:
                base = os.path.splitext(basename)[0]
                file = base + self.prof_ext
                if not os.path.exists(file):
                    outcome = self.FAIL
                    message = (self.GetId() + " execution: file "
                               + file + " does not exist, " + ostr)
            self._RecordDejaGNUOutcome(result, outcome, message)

            # Compile with feedback-directed optimization.
            o = options + [self.feedback_option]
            ostr = " ".join(o)
            message = self.GetId() + " execution,   " + ostr
            if outcome != self.PASS:
                compilation_message = self.GetId() + " compilation, " + ostr
                self._RecordDejaGNUOutcome(result, self.UNRESOLVED,
                                           compilation_message)
                self._RecordDejaGNUOutcome(result, self.UNRESOLVED,
                                           message)
                continue
            os.remove(execname1)
            output = self._Compile(context, result,
                                   [self._GetSourcePath()],
                                   execname2,
                                   "executable",
                                   o)

            # Run the executable.
            outcome = self._RunTargetExecutable(context, result, execname2)
            self._RecordDejaGNUOutcome(result, outcome, message)
            if outcome != self.PASS:
                continue

            self.__CleanUp(self.prof_ext)

            if not self.perf_ext:
                os.remove(execname2)
                continue

            raise NotImplementedError


    def _Compile(self, context, result, source_files, output_file,
                 mode, options):
        """Compile the 'source_files'.

        'context' -- The 'Context' in which the test is running.
        
        'result' -- The QMTest 'Result' for the test or resource.
        
        'source_files' -- A list of paths giving the source files to be
        compiled.

        'output_file' -- The name of the output file to be created.

        'mode' -- One of the 'Compiler.modes'.

        'options' -- A list of additional command-line options to be
        provided to the compiler.

        'test' -- The 'Test' object which is running, or 'None'.

        returns -- The output produced by the compiler."""

        raise NotImplementedError

                 
    def __CleanUp(self, extension):
        """Remove profiling data files with the indicated 'extension'

        'extension' -- The file name extension (including the leading
        period) for the files that should be removed."""

        basename = os.path.basename(self.GetId())
        base = os.path.splitext(basename)[0]
        files = glob.glob(base + extension)
        for f in files:
            os.remove(f)
