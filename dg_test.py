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
import fnmatch
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

    # The values of these constants have been chosen so that they
    # match the valid values for the 'dg-do' command.
    KIND_PREPROCESS = "preprocess"
    KIND_COMPILE = "compile"
    KIND_ASSEMBLE = "assemble"
    KIND_LINK = "link"
    KIND_RUN = "run"
    
    __test_kinds = (
        KIND_PREPROCESS,
        KIND_COMPILE,
        KIND_ASSEMBLE,
        KIND_LINK,
        KIND_RUN
        )
    """The kinds of tests supported by 'dg.exp'."""

    __diagnostic_descriptions = {
        "error" : "errors",
        "warning" : "warnings",
        "bogus" : "bogus messages",
        "build" : "build failure",
        }
    """A map from dg diagnostic kinds to descriptive strings."""
    
    executable_timeout = 300
    """The number of seconds a program is permitted to run on the target."""

    class TargetExecutable(TimeoutRedirectedExecutable):
        """A '__TargetExecutable' runs on the target system.

        Classes derived from 'DejaGNUTest' may provide derived
        versions of this class."""

        def __init__(self, timeout):

            # Initialize the base class.
            TimeoutRedirectedExecutable.__init__(self, 10)


        def _StdinPipe(self):

            # No input is provided to the program.
            return None

        
        def _StderrPipe(self):

            # Combine stdout/stderr into a single stream.
            return None
            
    

    def _RunDGTest(self, default_options, context, result):
        """Run a 'dg' test.

        'default_options' -- A string giving a default set of options
        to be provided to the tool being tested.  These options can be
        overridden by an embedded 'dg-options' command in the test
        itself.
        
        'context' -- The 'Context' in which this test is running.

        'result' -- The 'Result' of the test execution.

        This function emulates 'dg-test'."""
        
        # Intialize.
        self._kind = "compile"
        self._selected = None
        self._expectation = None
        self._options = default_options
        self._diagnostics = []
        self._final_commands = []
        # Iterate through the test looking for embedded commands.
        line_num = 0
        path = self._GetSourcePath()
        for l in open(path).xreadlines():
            line_num += 1
            m = self.__dg_command_regexp.search(l)
            if m:
                f = getattr(self, "_DGTest__DG" + m.group(1))
                args = self._ParseTclWords(m.group(2))
                f(line_num, args, context)

        # If this test does not need to be run on this target, stop.
        if self._selected == 0:
            self._RecordDejaGNUOutcome(result,
                                       self.UNSUPPORTED,
                                       self.GetId())
            return

        # Run the tool being tested.
        output, file = self._RunTool(self._kind, self._options, context,
                                     result)

        # Check to see if the right diagnostic messages appeared.
        # This algorithm takes time proportional to the number of
        # lines in the output times the number of expected
        # diagnostics.  One could do much better, but DejaGNU does
        # not.
        for l, k, x, p, c in self._diagnostics:
            # Remove all occurrences of this diagnostic from the
            # output.
            if l is not None:
                ldesc = "%d" % l
                l = ":%s:" % ldesc
            else:
                ldesc = ""
                l = ldesc
            output, matched = re.subn(r"(?m)^.+" + l + r".*(" + p + r").*$",
                                      "", output)
            # Record an appropriate test outcome.
            message = ("%s %s (test for %s, line %s)"
                       % (self.GetId(), c,
                          self.__diagnostic_descriptions[k], ldesc))
            if matched:
                outcome = self.PASS
            else:
                outcome = self.FAIL
            self._RecordDejaGNUOutcome(result, outcome, message, x)

        # Remove tool-specific messages that can be safely ignored.
        output = self._PruneOutput(output)
            
        # Remove leading blank lines.
        output = re.sub(r"\n+", "", output)
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
                    = self.TargetExecutable(self.executable_timeout)
                command = [file]
                index = self._RecordCommand(result, command)
                environment = self._GetTargetEnvironment(context)
                status = executable.Run([file], environment)
                output = executable.stdout
                self._RecordCommandOutput(result, index, status, output)
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
        for c, a in self._final_commands:
            self._ExecuteFinalCommand(c, a, context, result)

        # Remove the output file.
        try:
            os.remove(file)
        except:
            pass
                

    def _ExecuteFinalCommand(self, command, args, context, result):
        """Run a command specified with 'dg-final'.

        'command' -- A string giving the name of the command.
        
        'args' -- A list of strings giving the arguments (if any) to
        that command.

        'context' -- The 'Context' in which this test is running.

        'result' -- The 'Result' of this test."""

        raise NotImplementedError
        
        
    def _GetTargetEnvironment(self, context):
        """Return additional environment variables to set on the target.

        'context' -- The 'Context' in which this test is running.
        
        returns -- A map from strings (environment variable names) to
        strings (values for those variables).  These new variables are
        added to the environment when a program executes on the
        target."""

        return {}
    

    def _PruneOutput(self, output):
        """Remove unintersting messages from 'output'.

        'output' -- A string giving the output from the tool being
        tested.

        returns -- A modified version of 'output'.  This modified
        version does not contain tool output messages that are
        irrelevant for testing purposes."""

        raise NotImplementedError
    
        
    def _RunTool(self, kind, options, context, result):
        """Run the tool being tested.

        'kind' -- The kind of test to perform.

        'options' -- A string giving command-line options to provide
        to the tool.

        'context' -- The 'Context' for the test execution.

        'result' -- The QMTest 'Result' for the test.

        returns -- A pair '(output, file)' where 'output' consists of
        any messages produced by the compiler, and 'file' is the name
        of the file produced by the compilation, if any."""

        raise NotImplementedError
        
        
    def __DGdo(self, line_num, args, context):
        """Emulate the 'dg-do' command.

        'line_num' -- The line number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""

        if len(args) > 2:
            self._Error("dg-do: too many arguments")

        if len(args) >= 2:
            code = self._ParseTargetSelector(args[1], context)
            if code == "S":
                self._selected = 1
            elif code == "N":
                if self._selected != 1:
                    self._selected = 0
            elif code == "F":
                self._expectation = Result.FAIL
        else:
            self._selected = 1
            self._expectation = Result.PASS

        kind = args[0]
        if kind not in self.__test_kinds:
            self._Error("dg-do: syntax error")
            
        self._kind = kind


    def __DGfinal(self, line_num, args, context):
        """Emulate the 'dg-final' command.

        'line_num' -- The line number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""

        if len(args) > 1:
            self._Error("dg-final: too many arguments")

        words = self._ParseTclWords(args[0])
        self._final_commands.append((words[0], words[1:]))
            
        
    def __DGoptions(self, line_num, args, context):
        """Emulate the 'dg-options' command.

        'line_num' -- The line number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""

        if len(args) > 2:
            self._Error("'dg-options': too many arguments")

        if len(args) >= 2:
            code = self._ParseTargetSelector(args[1], context)
            if code == "S":
                self._options = args[0]
            elif code != "N":
                self._Error("'dg-options': 'xfail' not allowed here")
        else:
            self._options = args[0]


    def __DGwarning(self, line_num, args, context):
        """Emulate the 'dg-warning' command.

        'line_num' -- The number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""

        self.__ExpectDiagnostic("warning", line_num, args, context)

        
    def __DGerror(self, line_num, args, context):
        """Emulate the 'dg-error' command.

        'line_num' -- The number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""

        self.__ExpectDiagnostic("error", line_num, args, context)


    def __ExpectDiagnostic(self, kind, line_num, args, context):
        """Register an expected diagnostic.

        'kind' -- The kind of diagnostic expected.

        'line_num' -- The number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""

        if len(args) > 4:
            self._Error("'dg-" + kind + "': too many arguments")

        if len(args) >= 4:
            l = args[3]
            if l == "0":
                line_num = None
            elif l != ".":
                line_num = int(args[3])

        # Parse the target selector, if any.
        expectation = self.PASS
        if len(args) >= 3:
            code = self._ParseTargetSelector(args[2], context)
            if code == "N":
                return
            if code == "F":
                expectation = self.FAIL

        if len(args) >= 2:
            comment = args[1]
        else:
            comment = None
            
        self._diagnostics.append((line_num, kind, expectation,
                                  args[0], comment))
        
        
    def _ParseTargetSelector(self, selector, context):
        """Parse the target 'selector'.

        'selector' -- A target selector.

        'context' -- The 'Context' in which the test is running.

        returns -- For a 'target' selector, 'S' if this test should be
        run, or 'N' if it should not.  For an 'xfail' selector, 'F' if
        the test is expected to fail; 'P' if if not.

        This function emulates dg-process-target."""

        # Split the selector into words.
        words = selector.split()
        # Check the first word.
        if words[0] != "target" and words[0] != "xfail":
            raise QMException, "Invalid selector."
        # The rest of the selector is a space-separate list of
        # patterns.  See if any of them are matched by the current
        # target platform.
        target = self._GetTarget(context)
        match = 0
        for p in words[1:]:
            if (p == "native" and self._IsNative(context)
                or fnmatch.fnmatch(target, p)):
                match = 1
                break

        if words[0] == "target":
            if match:
                return "S"
            else:
                return "N"
        else:
            if match:
                return "F"
            else:
                return "P"
        
