########################################################################
#
# File:   dg_test.py
# Author: Mark Mitchell
# Date:   04/17/2003
#
# Contents:
#   DGTest
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   dejagnu_test import DejaGNUTest
import os
from   qm.executable import TimeoutRedirectedExecutable
from   qm.test.result import Result
import re

########################################################################
# Classes
########################################################################

class DGTest(DejaGNUTest):
    """A 'DGTest' is a test using the DejaGNU 'dg' driver.

    This test class emulates the 'dg.exp' source file in the DejaGNU
    distribution."""

    __dg_command_regexp \
         = re.compile(r"{[ \t]+dg-([-a-z]+)[ \t]+(.*)[ \t]+}[^}]*$")
    """A regular expression matching commands embedded in the source file."""

    __test_kinds = (
        "preprocess",
        "compile",
        "assemble",
        "link",
        "run"
        )
    """The kinds of tests supported by this test class."""

    executable_timeout = 300
    """The number of seconds a program is permitted to run on the target."""

    class __TargetExecutable(TimeoutRedirectedExecutable):
        """A '__TargetExecutable' runs on the target system."""

        def __init__(self, timeout):

            # Initialize the base class.
            TimeoutRedirectedExecutable.__init__(self, 10)


        def _StdinPipe(self):

            # No input is provided to the program.
            return None

        
        def _StderrPipe(self):

            # Combine stdout/stderr into a single stream.
            return None
            
    
    def Run(self, context, result):

        # Set up.
        self._SetUp(context)
        # This method emulates dg-test.
        path = self._GetSourcePath()
        # Intialize.
        self._kind = "compile"
        self._selected = None
        self._expectation = None
        self._diagnostics = []
        self._final_tests = []
        # Iterate through the test looking for embedded commands.
        line_num = 0
        for l in open(path).xreadlines():
            line_num += 1
            m = self.__dg_command_regexp.search(l)
            if m:
                f = getattr(self, "_DG" + m.group(1))
                args = self._ParseTclWords(m.group(2))
                f(line_num, args)

        # If this test does not need to be run on this target, stop.
        if self._selected == 0:
            self._RecordDejaGNUOutcome(self.UNSUPPORTED,
                                       self.GetId())
            return

        # Run the tool being tested.
        output, file = self._RunTool(self._kind, context, result)

        # Check to see if the right diagnostic messages appeared.
        for d in self._diagnostics:
            raise NotImplementedError

        # If there's any output left, the test fails.
        message = self.GetId() + " (test for excess errors)"
        if output != "":
            self._RecordDejaGNUOutcome(result, self.FAIL, message)
        else:
            self._RecordDejaGNUOutcome(result, self.PASS, message)

        # Run the generated program.
        if self._kind == "run":
            if not os.path.exists(file):
                message = (self.GetId()
                           + " compilation failed to produce executable")
                self._RecordDejaGNUOutcome(result, self.WARNING, message)
            else:
                executable \
                    = self.__TargetExecutable(self.executable_timeout)
                command = [file]
                self._RecordCommand(result, command)
                status = executable.Run([file])
                output = executable.stdout
                # Figure out whether the execution was successful.
                if os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0:
                    outcome = self.PASS
                else:
                    outcome = self.FAIL
                # Add an annotation indicating what happened.
                message = self.GetId() + " execution test"
                self._RecordDejaGNUOutcome(result, outcome, message,
                                           self._expectation)

        # Run dg-final tests.
        if self._final_tests:
            raise NotImplementedError

        # Remove the output file.
        try:
            os.remove(file)
        except:
            pass
                

    def _RunTool(self, kind, context, result):
        """Run the tool being tested.

        'kind' -- The kind of test to perform.

        'context' -- The 'Context' for the test execution.

        'result' -- The QMTest 'Result' for the test.

        returns -- A pair '(output, file)' where 'output' consists of
        any messages produced by the compiler, and 'file' is the name
        of the file produced by the compilation, if any."""

        raise NotImplementedError
        
        
    def _DGdo(self, line_num, args):
        """Emulate the 'dg-do' command.

        'line_num' -- The number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings."""

        if len(args) > 2:
            self._Error("dg-do: too many arguments")

        if len(args) >= 2:
            code = self._ParseTargetSelector(args[1])
            if code == "S":
                self._selected = 1
            elif code == "N":
                if self._selected != 0:
                    self._selected = 1
            elif code == "F":
                self._expectation = Result.FAIL
        else:
            self._selected = 1
            self._expectation = Result.PASS

        kind = args[0]
        if kind not in self.__test_kinds:
            self._Error("dg-do: syntax error")
            
        self._kind = kind
