########################################################################
#
# File:   dejagnu_test.py
# Author: Mark Mitchell
# Date:   04/16/2003
#
# Contents:
#   DejaGNUTest
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

import qm
from   qm.test.test import Test
from   qm.test.result import Result

########################################################################
# Classes
########################################################################

class DejaGNUTest(Test):
    """A 'DejaGNUTest' emulates a DejaGNU test.

    See 'framework.exp' in the DejaGNU distribution for more
    information."""

    arguments = [
        qm.fields.AttachmentField(
            name="source_file",
            title="Source File",
            description="""The source file."""),
        ]

    PASS = "PASS"
    FAIL = "FAIL"
    XPASS = "XPASS"
    XFAIL = "XFAIL"
    WARNING = "WARNING"
    UNTESTED = "UNTESTED"
    UNRESOLVED = "UNRESOLVED"
    UNSUPPORTED = "UNSUPPORTED"

    dejagnu_outcomes = (
        PASS, FAIL, XPASS, XFAIL, WARNING,
        UNTESTED, UNRESOLVED, UNSUPPORTED
        )
    """The DejaGNU test outcomes."""
    
    __outcome_map = {
        PASS : None,
        FAIL : Result.FAIL,
        XPASS : None,
        XFAIL : Result.FAIL,
        WARNING : None,
        UNTESTED : Result.UNTESTED,
        UNRESOLVED : Result.UNTESTED,
        UNSUPPORTED : Result.UNTESTED
        }
    """A map from DejaGNU outcomes to QMTest outcomes."""

    def _RecordCommand(self, result, command):
        """Record the execution of 'command'.

        'command' -- A sequence of strings, giving the arguments to a
        command that is about to be executed."""

        key = "DejaGNUTest.command_%d" % self.__next_command
        self.__next_command += 1
        result[key] = "<tt>" + " ".join(command) + "</tt>"
        
        
    def _RecordDejaGNUOutcome(self, result, outcome, message,
                              expectation = None):
        """Record a DejaGNU outcome.

        'result' -- A 'Result' object.

        'outcome' -- One of the 'dejagnu_outcomes'.

        'message' -- A string, explaining the outcome.

        'expectation' -- If not 'None, the DejaGNU outcome that was
        expected."""

        # If the test was expected to fail, transform PASS or FAIL
        # into XPASS or XFAIL, respectively.
        if expectation == self.FAIL:
            if outcome == self.PASS:
                outcome = self.XPASS
            elif outcome == self.FAIL:
                outcome = self.XFAIL

        # Create an annotation corresponding to the DejaGNU outcome.
        key = "DejaGNUTest.result_%d" % self.__next_result
        self.__next_result += 1
        result[key] = outcome + ": " + message
        # If the test was passing until now, give it a new outcome.
        new_outcome = self.__outcome_map[outcome]
        if (new_outcome and result.GetOutcome() == Result.PASS):
            result.SetOutcome(new_outcome)
            result[Result.CAUSE] = message
        

    def _Error(self, message):
        """Raise an exception indicating an error in the test.

        'message' -- A description of the problem.

        This function is used when the original Tcl code in DejaGNU
        would have used the Tcl 'error' primitive.  These situations
        indicate problems with the test itself, such as incorrect
        usage of special test commands."""

        raise DejaGNUError, message

        
    def _GetSourcePath(self):
        """Return the patch to the primary source file.

        returns -- A string giving the path to the primary source
        file."""

        return self.source_file.GetDataFile()


    def _SetUp(self, context):
        """Prepare to run a test.

        'context' -- The 'Context' in which this test will run.

        This method may be overridden by derived classes, but they
        must call this version."""

        # The next command will be the first.
        self.__next_command = 1
        # The next DejaGNU result will be the first.
        self.__next_result = 1

        
    def _ParseTclWords(self, s):
        """Separate 's' into words, in the same way that Tcl would.

        's' -- A string.

        returns -- A sequence of strings, each of which is a Tcl
        word.

        Some Tcl constructs (namely variable substitution and command
        substitution) are not supported and result in exceptions.
        Invalid inputs (like the string consisting of a single quote)
        also result in exceptions.
        
        See 'Tcl and the Tk Toolkit', by John K. Ousterhout, copyright
        1994 by Addison-Wesley Publishing Company, Inc. for details
        about the syntax of Tcl."""

        # There are no words yet.
        words = []
        # There is no current word.
        word = None
        # We are not processing a double-quoted string.
        in_double_quoted_string = 0
        # Nor are we processing a brace-quoted string.
        in_brace_quoted_string = 0
        # Iterate through all of the characters in s.
        while s:
            # See what the next character is.
            c = s[0]
            # A "$" indicates variable substitution.  A "[" indicates
            # command substitution.
            if (c == "$" or c == "[") and not in_brace_quoted_string:
                raise QMException, "Unsupported Tcl substitution."
            # A double-quote indicates the beginning of a double-quoted
            # string.
            elif c == '"' and not in_brace_quoted_string:
                # We are now entering a new double-quoted string, or
                # leaving the old one.
                in_double_quoted_string = not in_double_quoted_string
                # Skip the quote.
                s = s[1:]
                # The quote starts the word.
                if word is None:
                    word = ""
            # A "{" indicates the beginning of a brace-quoted string.
            elif c == '{' and not in_double_quoted_string:
                # If that's not the opening quote, add it to the
                # string.
                if in_brace_quoted_string:
                    if word is not None:
                        word = word + "{"
                    else:
                        word = "{"
                # The quote starts the word.
                if word is None:
                    word = ""
                # We are entering a brace-quoted string.
                in_brace_quoted_string += 1
                # Skip the brace.
                s = s[1:]
            elif c == '}' and in_brace_quoted_string:
                # Leave the brace quoted string.
                in_brace_quoted_string -= 1
                # Skip the brace.
                s = s[1:]
                # If that's not the closing quote, add it to the
                # string.
                if in_brace_quoted_string:
                    if word is not None:
                        word = word + "{"
                    else:
                        word = "{"
            # A backslash-newline is translated into a space.
            elif c == '\\' and len(s) > 1 and s[1] == '\n':
                # Skip the backslash and the newline.
                s = s[2:]
                # Now, skip tabs and spaces.
                while s and (s[0] == ' ' or s[0] == '\t'):
                    s = s[1:]
                # Now prepend one space.
                s = " " + s
            # A backslash indicates backslash-substitution.
            elif c == '\\' and not in_brace_quoted_string:
                # There should be a character following the backslash.
                if len(s) == 1:
                    raise QMException, "Invalid Tcl string."
                # Skip the backslash.
                s = s[1:]
                # See what the next character is.
                c = s[0]
                # If it's a control character, use the same character
                # in Python.
                if c in ["a", "b", "f", "n", "r", "t", "v"]:
                    c = eval('"\%s"' % c)
                    s = s[1:]
                # "\x" indicates a hex literal.
                elif c == "x":
                    raise QMException, "Unsupported Tcl escape."
                # "\d" where "d" is a digit indicates an octal literal.
                elif c.isdigit():
                    raise QMException, "Unsupported Tcl escape."
                # Any other character just indicates the character
                # itself.
                else:
                    s = s[1:]
                # Add it to the current word.
                if word is not None:
                    word = word + c
                else:
                    word = c
            # A space or tab indicates a word separator.
            elif ((c == ' ' or c == '\t')
                  and not in_double_quoted_string
                  and not in_brace_quoted_string):
                # Add the current word to the list of words.
                if word is not None:
                    words.append(word)
                # Skip over the space.
                s = s[1:]
                # Keep skipping while the leading character of s is
                # a space or tab.
                while s and (s[0] == ' ' or s[0] == '\t'):
                    s = s[1:]
                # Start the next word.
                word = None
            # Any other character is just added to the current word.
            else:
                if word is not None:
                    word = word + c
                else:
                    word = c
                s = s[1:]

        # If we were working on a word when we reached the end of
        # the stirng, add it to the list.
        if word is not None:
            words.append(word)

        return words
