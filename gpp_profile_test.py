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

import gpp
from   profile_test import ProfileTest

########################################################################
# Classes
########################################################################

class GPPProfileTest(ProfileTest):
    """A 'GPPProfileTest' is a G++ profiling test."""

    prof_ext = ".da"

    feedback_option = "-fbranch-probabilities"

    profile_option = "-fprofile-arcs"

    def _Compile(self, context, result, source_files, output_file,
                 mode, options):

        return gpp.compile(context, result, source_files, output_file, mode,
                           options, self)


    def _GetTargetEnvironment(self, context):

        return gpp.get_target_environment(context)
