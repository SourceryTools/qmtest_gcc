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
from   qm.test.file_database import FileDatabase
from   qm.test.directory_suite import DirectorySuite
from   qm.test.runnable import Runnable

########################################################################
# Classes
########################################################################

class GCCDatabase(FileDatabase):
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
        ]
    
    __test_class_map = (
        (os.path.join("gcc.dg", "noncompile"),
         "gcc_dg_test.GCCDGNoncompileTest"),
        (os.path.join("gcc.dg", "debug"),
         "debug_test.GCCDGDebugTest"),
        ("gcc.dg",
         "gcc_dg_test.GCCDGTest"),
        (os.path.join("g++.dg", "bprob"),
         "gpp_profile_test.GPPProfileTest"),
        (os.path.join("g++.dg", "tls"),
         "gpp_dg_tls_test.GPPDGTLSTest"),
        (os.path.join("g++.dg", "compat"),
         "gpp_compat_test.GPPCompatTest"),
        (os.path.join("g++.dg", "debug"),
         "debug_test.GPPDGDebugTest"),
        (os.path.join("g++.dg", "gcov"),
         "gpp_gcov_test.GPPGCOVTest"),
        (os.path.join("g++.dg", "pch"),
         "gpp_dg_pch_test.GPPDGPCHTest"),
        ("g++.dg",
         "gpp_dg_test.GPPDGTest"),
        ("g++.old-deja",
         "gpp_old_deja_test.GPPOldDejaTest")
        )
    """A map from test name prefixes to test classes.

    The databases determines which test class to use for a particular
    test by scanning this list.  The test class used is the one
    associated with the first matching prefix."""

    def __init__(self, path, arguments):

        # Initialize the base class.
        super(GCCDatabase, self).__init__(path, arguments)
        # Create an attachment store.
        self.__store = FileAttachmentStore(self)

        
    def GetResource(self, resource_id):

        if resource_id == "compiler_table":
            return ResourceDescriptor(self, resource_id,
                                      "compiler_table.CompilerTable",
                                      {})
        elif resource_id == "gpp_init":
            return ResourceDescriptor(self, resource_id,
                                      "gpp_init.GPPInit",
                                      { Runnable.RESOURCE_FIELD_ID :
                                        ["compiler_table"] })
        elif resource_id == os.path.join("g++.dg", "tls", "init"):
            return ResourceDescriptor(self, resource_id,
                                      "gpp_tls_init.GPPTLSInit",
                                      { Runnable.RESOURCE_FIELD_ID :
                                        ["gpp_init"] })
        elif resource_id == os.path.join("g++.dg", "debug", "init"):
            return ResourceDescriptor(self, resource_id,
                                      "debug_test.GPPDebugInit",
                                      { Runnable.RESOURCE_FIELD_ID :
                                        ["gpp_init"] })
        elif resource_id == os.path.join("gcc.dg", "debug", "init"):
            return ResourceDescriptor(self, resource_id,
                                      "debug_test.GCCDebugInit",
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

        resources = []
        
        # All G++ tests depend on gpp_init.
        if test_id.startswith("g++."):
            resources.append("gpp_init")
        elif test_id.startswith("gcc."):
            resources.append("compiler_table")
        # The TLS tests depend on tls_init.
        if test_id.startswith(os.path.join("g++.dg", "tls")):
            resources.append(os.path.join("g++.dg", "tls", "init"))
        elif test_id.startswith(os.path.join("g++.dg", "debug")):
            resources.append(os.path.join("g++.dg", "debug", "init"))
        elif test_id.startswith(os.path.join("gcc.dg", "debug")):
            resources.append(os.path.join("gcc.dg", "debug", "init"))
        # Create the test descriptor.
        descriptor = TestDescriptor(self, test_id, test_class,
                                    { 'source_file' : attachment,
                                      Runnable.RESOURCE_FIELD_ID :
                                        resources })

        return descriptor
        
                
        
    def _IsFile(self, kind, path):

        # Suites are directories.
        if kind == self.SUITE:
            return os.path.isdir(path)

        # No resources are stored in files.
        if kind == self.RESOURCE:
            return 0

        rel_path = path[len(self.GetRoot()):]
        if rel_path.startswith(os.path.join(os.sep, "gcc")):
            return os.path.splitext(path)[1] == ".c"

        # In the g++.dg/compat subdirectory, only tests that end with
        # _main.C are tests.
        if rel_path.startswith(os.sep + os.path.join("g++.dg", "compat")):
            return rel_path.endswith("_main.C")
                            
        if rel_path.startswith(os.path.join(os.sep, "g++")):
            return os.path.splitext(path)[1] == ".C"

        return 0
    
            
