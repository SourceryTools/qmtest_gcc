########################################################################
#
# File:   compat_test.py
# Author: Mark Mitchell
# Date:   05/02/2003
#
# Contents:
#   CompatTest
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   dejagnu_test import DejaGNUTest
import os
import re

########################################################################
# Classes
########################################################################

class CompatTest(DejaGNUTest):
    """A 'CompatTest' emulates the 'compat.exp' test driver."""

    __options_regexp \
          = re.compile(r"{[ \t]*dg-options[ \t]+(.*)[ \t]+}")
    """A regular expression that matches an options directive in the test.

    If this regular expression matches the main test-case file, then
    the first match group gives special options that should be used to
    run the test-case."""
    
    def Run(self, context, result):

        self._SetUp(context)

        # Figure out whether or not there is an alternate compiler.
        use_alt = context.has_key("CompatTest.use_alt")
        if use_alt:
            raise NotImplementedError
        
        # Get the dg-options string out of the test.
        src1 = self._GetSourcePath()
        match = self.__options_regexp.search(open(src1).read())
        if match:
            extra_options = self._ParseTclWords(match.group(1))[0].split()
        else:
            extra_options = []

        base = os.path.basename(src1)
        base = re.sub("_main.*", src1, "")
        src2 = src1.replace("_main", "_x")
        src3 = src1.replace("_main", "_y")

        temp_dir = context.GetTemporaryDirectory()
        obj1 = os.path.join(temp_dir, "main_tst.o")
        obj2_tst = os.path.join(temp_dir, "x_tst.o")
        obj2_alt = os.path.join(temp_dir, "x_alt.o")
        obj3_tst = os.path.join(temp_dir, "y_tst.o")
        obj3_alt = os.path.join(temp_dir, "y_alt.o")

        self._testcase = re.sub("_main.*", "", self.GetId())
        execbase = os.path.join(temp_dir,
                                self._testcase.replace(os.sep, "-"))

        count = 0
        option_list = [("", "")]
        for tst_option, alt_option in option_list:
            if tst_option or alt_option:
                optstr = '"%s", "%s"' % (tst_option, alt_option)
            else:
                optstr = ""

            tst_options = []
            alt_options = []
            if extra_options:
                tst_options = extra_options
                if tst_option:
                    tst_options.append(tst_option)
                alt_options = extra_options
                if alt_option:
                    tst_options.append(alt_option)

            execname1 = "%s-%d1" % (execbase, count)
            execname2 = "%s-%d2" % (execbase, count)
            execname3 = "%s-%d3" % (execbase, count)
            execname4 = "%s-%d4" % (execbase, count)
            count += 1

            for f in (execname1, execname2, execname3, execname4):
                try:
                    os.path.remove(execname1)
                except:
                    pass

            if use_alt:
                self.__GenerateObject(result, context, src2, obj2_alt,
                                      alt_options, optstr, alt = 1)
                self.__GenerateObject(result, context, src3, obj3_alt,
                                      alt_options, optstr, alt = 1)

            self.__GenerateObject(result, context, src1, obj1,
                                  tst_options, optstr)
            self.__GenerateObject(result, context, src2, obj2_tst,
                                  tst_options, optstr)
            self.__GenerateObject(result, context, src3, obj3_tst,
                                  tst_options, optstr)

            self.__Run(result, context, obj2_tst + "-" + obj3_tst,
                       [obj1, obj2_tst, obj3_tst],
                       execname1, tst_options, optstr)

            if use_alt:
                self.__Run(result, context, obj2_tst + "-" + obj3_alt,
                           [obj1, obj2_tst, obj3_alt],
                           execname2, tst_options, optstr)
                self.__Run(result, context, obj2_alt + "-" + obj3_tst,
                           [obj1, obj2_alt, obj3_tst],
                           execname3, tst_options, optstr)
                self.__Run(result, context, obj2_alt + "-" + obj3_alt,
                           [obj1, obj2_alt, obj3_alt],
                           execname4, tst_options, optstr)

            # Clean up glue files.
            for x in (obj1, obj2_tst, obj2_alt, obj3_tst, obj3_alt):
                try:
                    os.remove(x)
                except:
                    pass


    def __GenerateObject(self, result, context, source, dest,
                         options, optstr, alt = 0):
        """Emulate 'compat-obj'.

        'result' -- The QMTest 'Result'.

        'context' -- The QMTest 'context'.

        'source' -- The path to the source file to compile.

        'dest' -- The path to the object file to generate.

        'options' -- The options to use when compiling the test.

        'optstr' -- A descripion of the options."""
        
        if alt:
            raise NotImplementedError
        
        self._CheckCompile(result,
                           "%s %s compile" % (self._testcase, dest),
                           optstr, dest,
                           self._Compile(context, result, [source],
                                         dest, "object", options))


    def __Run(self, result, context, testname, objlist, dest, options,
              optstr):
        """Emulate 'compat-run'.

        'result' -- The QMTest 'Result'.

        'context' -- The QMTest 'context'.

        'testname' -- The name of the test.

        'objlist' -- A list of strings giving the name of object files
        to link together.

        'dest' -- The name of the executable to create.

        'options' -- The compilation options to use when linking the
        objects together.

        'optstr' -- A description of the options."""
        
        link_message = "%s %s link %s" % (self._testcase, testname, optstr)
        exec_message = "%s %s execute %s" % (self._testcase, testname, optstr)

        for obj in objlist:
            if not os.path.exists(obj):
                self._Unresolved(result, link_message)
                self._Unresolved(result, exec_message)
                return

        if not self._CheckCompile(result,
                                  link_message,
                                  optstr, dest,
                                  self._Compile(context, result, objlist, dest,
                                                "executable",
                                  options)):
            self._Unresolved(result, exec_message)
            return

        if "/" not in dest:
            dest = os.path.join(".", dest)
        outcome = self._RunTargetExecutable(context, result, dest)
        if outcome == self.PASS:
            os.remove(dest)
        self._RecordDejaGNUOutcome(result, outcome, exec_message)
    
                 
