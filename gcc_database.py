########################################################################
#
# File:   gcc_database.py
# Author: Mark Mitchell
# Date:   04/16/2003
#
# Contents:
#   GCCDatabase
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   gpp_dg_test import GPPDGTest
from   old_dejagnu_test import OldDejaGNUTest
import os
import qm
from   qm.attachment import Attachment, FileAttachmentStore
from   qm.test.database import ResourceDescriptor, TestDescriptor
from   qm.test.file_database import ExtensionDatabase
from   qm.test.directory_suite import DirectorySuite
from   qm.test.runnable import Runnable

########################################################################
# Classes
########################################################################

class GPPDatabase(ExtensionDatabase):
    """A 'GPPDatabase' stores the G++ regression tests."""

    arguments = [
        qm.fields.TextField(
            name = "srcdir",
            title = "Source Directory",
            description ="""The root of the G++ test source directory.

            This directory is the one that contains 'g++.dg' and
            'g++.old-deja'."""),
        # The G++ database uses filenames as labels.
        qm.fields.TextField(
            name = "label_class",
            default_value = "file_label.FileLabel",
            computed = "true"
            ),
        # The G++ database cannot be modified programmatically.
        qm.fields.BooleanField(
            name = "modifiable",
            default_value = "false",
            computed = "true",
            ),
        # Tests use the ".C" extension.
        qm.fields.TextField(
            name = "test_extension",
            default_value = ".C",
            computed = "true",
            ),
        # Suites have no extension.
        qm.fields.TextField(
            name = "suite_extension",
            default_value = "",
            computed = "true",
            ),
        ]
    
    __test_class_map = (
        ("g++.dg", "gpp_dg_test.GPPDGTest"),
        ("g++.old-deja", "old_dejagnu_test.OldDejaGNUTest")
        )
    """A map from test name prefixes to test classes.

    The databases determines which test class to use for a particular
    test by scanning this list.  The test class used is the one
    associated with the first matching prefix."""

    def __init__(self, path, arguments):

        # Initialize the base class.
        ExtensionDatabase.__init__(self, path, arguments)
        # Create an attachment store.
        self.__store = FileAttachmentStore(self)

        
    def GetResource(self, resource_id):

        # There are two special resources that are used for
        # initialization.
        if resource_id == "compiler_table":
            return ResourceDescriptor(self, resource_id,
                                      "compiler_table.CompilerTable",
                                      {})
        elif resource_id == "gpp_init":
            return ResourceDescriptor(self, resource_id,
                                      "gpp_init.GPPInit",
                                      { Runnable.RESOURCE_FIELD_ID :
                                        ["compiler_table"] })

        raise database.NoSuchResourceError, resource_id
        
        
    def GetRoot(self):

        return self.srcdir


    def GetAttachmentStore(self):

        return self.__store


    def _GetSuiteFromPath(self, suite_id, path):

        return DirectorySuite(self, suite_id)


    def _GetTestFromPath(self, test_id, path):

        # Figure out which test class to use.
        p = path[len(self.GetRoot()) + 1:]
        for prefix, test_class in self.__test_class_map:
            if p.startswith(prefix):
                break

        # Construct the attachment representing the primary source
        # file.
        basename = os.path.basename(path)
        attachment = Attachment("text/plain", basename,
                                basename, path,
                                self.GetAttachmentStore())

        # Create the test descriptor.
        descriptor = TestDescriptor(self, test_id, test_class,
                                    { 'source_file' : attachment,
                                      # All tests depend on the
                                      # compiler table.
                                      Runnable.RESOURCE_FIELD_ID :
                                        ["gpp_init"] })

        return descriptor
        
                
        
    def _IsFile(self, kind, path):

        val = ExtensionDatabase._IsFile(self, kind, path)

        # Non-directories are not suites.
        if val and kind == ExtensionDatabase.SUITE and not os.path.isdir(path):
            return 0

        return val
    
            
