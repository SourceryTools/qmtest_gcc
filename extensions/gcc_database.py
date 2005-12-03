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

import fnmatch
import os
import qm
import qm.test.base
from   qm.attachment import Attachment, FileAttachmentStore
from   qm.test.database import ResourceDescriptor, TestDescriptor
from   qm.test.file_database import FileDatabase
from   qm.test.directory_suite import DirectorySuite
from   qm.test.runnable import Runnable

import maximal_prefix

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
    
    _j = os.path.join
    __test_class_map = {
        # GCC tests:
        "gcc.dg": "gcc_dg_test.GCCDGTest",
        _j("gcc.c-torture", "compile"):
            "gcc_dg_test.GCCCTortureCompileTest",
        _j("gcc.c-torture", "unsorted"):
            "gcc_dg_test.GCCCTortureCompileTest",
        _j("gcc.dg", "compat"): "compat_test.GCCCompatTest",
        _j("gcc.dg", "cpp", "trad"): "gcc_dg_test.GCCDGCPPTradTest",
        _j("gcc.dg", "cpp"): "gcc_dg_test.GCCDGCPPTest",
        _j("gcc.dg", "debug"): "debug_test.GCCDGDebugTest",
        _j("gcc.dg", "format"): "gcc_dg_test.GCCDGFormatTest",
        _j("gcc.dg", "noncompile"): "gcc_dg_test.GCCDGNoncompileTest",
        _j("gcc.dg", "pch"): "dg_pch_test.GCCDGPCHTest",
        _j("gcc.dg", "tls"): "dg_tls_test.GCCDGTLSTest",
        _j("gcc.dg", "torture"): "gcc_dg_test.GCCDGTortureTest", 
        # G++ tests:
        "g++.dg": "gpp_dg_test.GPPDGTest",
        _j("g++.dg", "bprob"): "gpp_profile_test.GPPProfileTst",
        _j("g++.dg", "tls"): "dg_tls_test.GPPDGTLSTet",
        _j("g++.dg", "compat"): "compat_test.GPPCompatTest",
        _j("g++.dg", "debug"): "debug_test.GPPDGDebugTest",
        _j("g++.dg", "gcov"): "gpp_gcov_test.GPPGCOVTest",
        _j("g++.dg", "pch"): "dg_pch_test.GPPDGPCHTest",
        "g++.old-deja": "gpp_old_deja_test.GPPOldDejaTest"
        }
    """A map from test name prefixes to test classes.

    The databases determines which test class to use for a particular
    test by finding the longest entry in this table which is a prefix of
    the test's filename."""

    def __init__(self, path, arguments):

        # Initialize the base class.
        super(GCCDatabase, self).__init__(path, arguments)
        # Create an attachment store.
        self.__store = FileAttachmentStore()
        # Create the prefix matcher.
        self.__matcher = maximal_prefix.MaximalPrefixMatcher()
        self.__matcher.add(self.__test_class_map)

        
    def GetResource(self, resource_id):

        if resource_id == "compiler_table":
            return ResourceDescriptor(self, resource_id,
                                      "compiler_table.CompilerTable",
                                      {})
        elif resource_id == "gcc_init":
            return ResourceDescriptor(self, resource_id,
                                      "gcc_init.GCCInit",
                                      { Runnable.RESOURCE_FIELD_ID :
                                        ["compiler_table"] })
        elif resource_id == "gpp_init":
            return ResourceDescriptor(self, resource_id,
                                      "gpp_init.GPPInit",
                                      { Runnable.RESOURCE_FIELD_ID :
                                        ["compiler_table"] })
        elif resource_id == os.path.join("gcc.dg", "tls", "init"):
            return ResourceDescriptor(self, resource_id,
                                      "dg_tls_test.GCCTLSInit",
                                      { Runnable.RESOURCE_FIELD_ID :
                                        ["compiler_table"] })
        elif resource_id == os.path.join("g++.dg", "tls", "init"):
            return ResourceDescriptor(self, resource_id,
                                      "dg_tls_test.GPPTLSInit",
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
            

        raise self.NoSuchResourceError, resource_id
        
        
    def GetRoot(self):

        return self.srcdir


    def GetAttachmentStore(self):

        return self.__store


    def GetSuite(self, suite_id):

        suite_class = qm.test.base.get_extension_class(
            "explicit_suite.ExplicitSuite", "suite", self)
        extras = { suite_class.EXTRA_DATABASE: self,
                   suite_class.EXTRA_ID: suite_id }
        arguments = { "is_implicit": 1,
                      "test_ids": [] }
                   
        if suite_id == "g++":
            arguments["suite_ids"] = ["g++.dg", "g++.old-deja"]
            return suite_class(arguments, **extras)
        elif suite_id == "gcc":
            arguments["suite_ids"] = ["gcc.dg"]
            return suite_class(arguments, **extras)

        return super(GCCDatabase, self).GetSuite(suite_id)
                     
        
    def _GetTestFromPath(self, test_id, path):

        # Figure out which test class to use.
        p = path[len(self.GetRoot()) + 1:]
        prefix = self.__matcher[p]
        test_class = self.__test_class_map[prefix]

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
            resources.append("gcc_init")
        # The TLS tests depend on tls_init.
        if test_id.startswith(os.path.join("gcc.dg", "tls")):
            resources.append(os.path.join("gcc.dg", "tls", "init"))
        elif test_id.startswith(os.path.join("g++.dg", "tls")):
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
        
                

    def _IsResourceFile(self, path):

        # No resources are stored in files.
        return 0

        
    def _IsSuiteFile(self, path):

        # All directories are suites.
        return os.path.isdir(path)

        
    def _IsTestFile(self, path):

        rel_path = path[len(self.GetRoot()):]

        # In the gcc.dg/compat subdirectory, only tests that end with
        # _main.c are tests.
        if rel_path.startswith(os.sep + os.path.join("gcc.dg", "compat")):
            return rel_path.endswith("_main.c")

        # If the gcc.dg/special subdirectory, only some source files
        # are tests.
        if rel_path.startswith(os.sep + os.path.join("gcc.dg", "special")):
            return fnmatch.fnmatch(rel_path, "*[1-9].c")
                
        if rel_path.startswith(os.path.join(os.sep, "gcc")):
            return os.path.splitext(path)[1] == ".c"

        # In the g++.dg/compat subdirectory, only tests that end with
        # _main.C are tests.
        if rel_path.startswith(os.sep + os.path.join("g++.dg", "compat")):
            return rel_path.endswith("_main.C")
                            
        if rel_path.startswith(os.path.join(os.sep, "g++")):
            return os.path.splitext(path)[1] == ".C"

        return 0
    
            
