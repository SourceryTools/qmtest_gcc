########################################################################
#
# File:   gpp_profile_test.py
# Author: Mark Mitchell
# Date:   04/21/2003
#
# Contents:
#   GPPProfileTest
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   gpp_test_base import GPPTestBase
from   profile_test import ProfileTest

########################################################################
# Classes
########################################################################

class GPPProfileTest(ProfileTest, GPPTestBase):
    """A 'GPPProfileTest' is a G++ profiling test."""

    prof_ext = ".da"

    feedback_option = "-fbranch-probabilities"

    profile_option = "-fprofile-arcs"

    def _Compile(self, context, result, source_files, output_file,
                 mode, options):

        return GPPTestBase._Compile(self, context, result,
                                    source_files, output_file, mode,
                                    options)


    def _GetTargetEnvironment(self, context):

        return GPPTestBase._GetTargetEnvironment(self, context)
