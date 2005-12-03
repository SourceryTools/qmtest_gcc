########################################################################
#
# File:   v3_database.py
# Author: Nathaniel Smith
# Date:   03/01/2004
#
# Contents:
#   V3Database
#
# Copyright (c) 2004 by CodeSourcery, LLC.  All rights reserved. 
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
from   qm.test.runnable import Runnable

########################################################################
# Classes
########################################################################

class V3Database(FileDatabase):
    """A 'V3Database' stores the libstc++-v3 regression tests."""

    arguments = [
        qm.fields.TextField(
            name = "srcdir",
            title = "Source Directory",
            description ="""The root of the libstdc++-v3 test source directory.

            This directory is the one named 'testsuite'."""),
        # The libstdc++ database uses filenames as labels.
        qm.fields.TextField(
            name = "label_class",
            default_value = "file_label.FileLabel",
            computed = "true"
            ),
        # The libstdc++ database cannot be modified programmatically.
        qm.fields.BooleanField(
            name = "modifiable",
            default_value = "false",
            computed = "true",
            ),
        ]
    
    def __init__(self, path, arguments):

        # Initialize the base class.
        super(V3Database, self).__init__(path, arguments)
        # Create an attachment store.
        self.__store = FileAttachmentStore()

        
    def GetResource(self, resource_id):

        if resource_id == "compiler_table":
            return ResourceDescriptor(self, resource_id,
                                      "compiler_table.CompilerTable",
                                      {})
        elif resource_id == "v3_init":
            return ResourceDescriptor(self, resource_id,
                                      "v3_test.V3Init",
                                      { Runnable.RESOURCE_FIELD_ID :
                                        ["compiler_table"] })

        raise self.NoSuchResourceError, resource_id
        
        
    def GetRoot(self):

        return self.srcdir


    def GetAttachmentStore(self):

        return self.__store


    def GetTestIds(self, directory="", scan_subdirs=1):

        result = super(V3Database, self).GetTestIds(directory,
                                                    scan_subdirs)
        if directory == "":
            return result + ["v3_abi_test"]
        else:
            return result


    def GetTest(self, test_id):

        if test_id == "v3_abi_test":
            return TestDescriptor(self, test_id,
                                  "v3_test.V3ABITest",
                                  { Runnable.RESOURCE_FIELD_ID:
                                    ["v3_init"]})
        else:
            return super(V3Database, self).GetTest(test_id)
        

    def _GetTestFromPath(self, test_id, path):

        # Construct the attachment representing the primary source
        # file.
        basename = os.path.basename(path)
        attachment = Attachment("text/plain", basename,
                                basename, path,
                                self.GetAttachmentStore())

        # Create the test descriptor.
        resources = ["v3_init"]
        descriptor = TestDescriptor(self, test_id,
                                    "v3_test.V3DGTest",
                                    { 'source_file' : attachment,
                                      Runnable.RESOURCE_FIELD_ID :
                                        resources })

        return descriptor
        
                

    def _IsResourceFile(self, path):

        # No resources are stored in files.
        return False

        
    def _IsSuiteFile(self, path):

        # All directories are suites.
        return os.path.isdir(path)

        
    def _IsTestFile(self, path):
        """This function emulates scripts/create_testsuite_files."""

        assert path.startswith(self.GetRoot() + os.sep)

        rel_path = path[len(self.GetRoot()) + 1:]
        if os.sep not in rel_path:
            return False

        if not rel_path.endswith(".cc"):
            return False

        forbidden_substrings = ["_xin", "performance"]
        # FIXME: create_testsuite_files checks to see if wchar_t support
        # is enabled (by checking for the existence of
        # $outdir/testsuite_wchar_t), and if it isn't, then "wchar_t" is
        # added to the forbidden list.  The right way to handle this in
        # QMTest is not obvious, so for now we ignore this.
        for f in forbidden_substrings:
            if rel_path.find(f) != -1:
                return False

        return True
