########################################################################
#
# File:   v3_test.py
# Author: Nathaniel Smith
# Date:   03/08/2004
#
# Contents:
#   V3Init, V3DGTest, V3ABICheck
#
# Copyright (c) 2004 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

import shutil
import fnmatch
import glob
import os
import os.path
import re
import qm
from qm.executable import RedirectedExecutable
from qm.test.test import Test
from qm.test.resource import Resource
from dg_test import DGTest
from dejagnu_base import DejaGNUBase
from qm.test.result import Result
from gcc_test_base import GCCTestBase
from compiler import CompilerExecutable

########################################################################
# Classes
########################################################################

_ld_library_path_names = ["LD_LIBRARY_PATH", "SHLIB_PATH",
                          "LD_LIBRARYN32_PATH", "LD_LIBRARY64_PATH",
                          "LD_RUN_PATH", "LD_LIBRARY_PATH_32",
                          "LD_LIBRARY_PATH_64", "DYLD_LIBRARY_PATH"]
"""All the different envvars that might mean LD_LIBRARY_PATH."""

class V3Init(Resource):
    """All V3 tests depend on one of these for setup."""

    def SetUp(self, context, result):

        # Get general information that will be used through the rest of
        # the setup.
        srcdir = self.GetDatabase().GetRoot()
        target = context["DejaGNUTest.target"]

        # Are we using the standalone testsuite to test an installed
        # libstdc++/g++, or the integrated testsuite to test a
        # just-built libstdc++/g++?  Check for the magic file that the
        # standalone package contains.
        standalone_marker = os.path.join(srcdir, "..",
                                         "THIS-IS-STANDALONE-V3")
        standalone = os.path.exists(standalone_marker)
        if standalone:
            standalone_root = os.path.join(srcdir, "..")
        context["V3Init.is_standalone"] = standalone

        # Find the compiler.
        compilers = context["CompilerTable.compiler_table"]
        compiler = compilers["cplusplus"]


        if not standalone:
            # Find blddir and outdir, and make outdir available to later
            # tests.
            options = compiler.GetOptions()
            compiler_executable = CompilerExecutable()
            compiler_executable.Run([compiler.GetPath()]
                                    + options
                                    + ['--print-multi-dir'])
            directory = compiler_executable.stdout[:-1]
            
            for o in options:
                if o.startswith("-B"):
                    # Calling 'normpath' is necessary to remove any possible
                    # trailing /.
                    objdir = os.path.dirname(os.path.normpath(o[2:]))
                    break
                else:
                    result.SetOutcome(result.ERROR,
                                      "Cannot find build directory; no -B in "
                                      "compiler options")
                    return

            objdir = os.path.abspath(objdir)
            blddir = os.path.normpath(os.path.join(objdir,
                                                   target,
                                                   directory,
                                                   "libstdc++-v3"))
            outdir = os.path.join(blddir, "testsuite")
        else:
            # User must provide build directory.
            # Our code always refers to this directory as 'outdir' for
            # parallelism with the DejaGNU code we emulate, but we call
            # it "scratch_dir" for UI purposes.
            if context.has_key("V3Init.outdir"):
                result.SetOutcome(result.ERROR,
                                  "Set V3Init.scratch_dir, not outdir")
                return
            outdir = context["V3Init.scratch_dir"]
            outdir = os.path.abspath(outdir)
            if not os.path.exists(outdir):
                os.mkdir(outdir)
            
        context["V3Init.outdir"] = outdir

#         print "options = %s" % repr(options)
#         print "directory = '%s'" % directory
#         print "objdir = '%s'" % objdir
#         print "target = '%s'" % target
#         print "blddir = '%s'" % blddir
#         print "outdir = '%s'" % outdir
#         print "srcdir = '%s'" % srcdir

        # Ensure that the message format files are available.
        # This requires different commands depending on whether we're
        # using the gcc build system or not.
        if not standalone:
            locale_dir = os.path.join(blddir, "po")
            make_command = ["make", "-j1", "check"]
        else:
            # Standalone build needs to set up the locale stuff in its
            # own directory.
            locale_dir = os.path.join(outdir, "qm_locale")
            try:
                os.mkdir(locale_dir)
            except OSError:
                pass
            makefile_in = open(os.path.join(standalone_root,
                                                  "qm-misc",
                                                  "locale-Makefile"))
            makefile_str = makefile_in.read()
            makefile_str = makefile_str.replace("@ROOT@",
                                                standalone_root)
            makefile_out = open(os.path.join(locale_dir, "Makefile"),
                                "w")
            makefile_out.write(makefile_str)
            makefile_out.close()
            make_command = ["make", "-j1", "locales"]

        make_executable = RedirectedExecutable()
        status = make_executable.Run(make_command, dir=locale_dir)
        if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
            result.SetOutcome(result.ERROR,
                              "Error building locale information",
                              {"status": str(status),
                               "stdout": "<pre>"
                                         + make_executable.stdout
                                         + "</pre>",
                               "stderr": "<pre>"
                                         + make_executable.stderr
                                         + "</pre>",
                               "command": " ".join(make_command),
                               })
            return
            

        # Copy data files.
        for file in "*.tst", "*.txt":
            if os.path.isdir(os.path.join(srcdir, "data")):
                # 3.4+ store these files in a special data/ directory.
                subdirs = ["data"]
            else:
                # But earlier versions store them scattered through the
                # tree.
                subdirs = ["*", os.path.join("*", "*")]
            for subdir in subdirs:
                for f in glob.glob(os.path.join(srcdir, subdir, file)):
                    shutil.copy(f, outdir)
        
        # Set up environment and -L switches.
        for name in _ld_library_path_names:
            if os.environ.has_key(name):
                original_ld_library_path = os.environ[name].split(":")
                break
        else:
            original_ld_library_path = []
        libpaths = []
        # Each branch sets ld_library_path and modifies libpaths.
        if not standalone:
            gccdir = os.path.join(objdir, "gcc")
            libpaths.append(gccdir)
            command = compiler.GetPath()
            compiler_executable.Run([compiler.GetPath()]
                                    + options
                                    + ["--print-multi-lib"])
            for line in compiler_executable.stdout.split():
                dir, args = line.split(";", 1)
                if dir == ".":
                    continue
                if glob.glob(os.path.join(gccdir, dir, "libgcc_s*.so.*")):
                    libpaths.append(dir)

            libpaths.append(os.path.join(blddir, "src", ".libs"))
            ld_library_path = ":".join(libpaths + original_ld_library_path)
        else:

            ld_library_path = ":".join(original_ld_library_path)

        libpaths.append(outdir)
        context["V3Init.libpaths"] = libpaths
        context["V3Init.ld_library_path"] = ld_library_path
        result["V3Init.ld_library_path"] = ld_library_path

        # Calculate default g++ flags.  Both branches create basic_flags
        # and default_flags.
        if not standalone:
            # Use the build tree mechanisms.
            try:
                all_flags = self._CalcBuildTreeFlags(result, context,
                                                     blddir, compiler)
            except:
                result.NoteException(cause="Error calculating default flags",
                                     outcome=Result.FAIL)
                return
            basic_flags, default_flags = all_flags
        else:
            # We take the union of the 3.3 and the 3.4 defines; it
            # doesn't seem to hurt.
            basic_flags = [# v3.4 only:
                           "-D_GLIBCXX_ASSERT",
                           # v3.3 only:
                           "-DDEBUG_ASSERT",
                           # Common:
                           "-g", "-O2",
                           "-ffunction-sections", "-fdata-sections",
                           "-fmessage-length=0",
                           "-DLOCALEDIR=\"%s\"" % locale_dir,
                           "-I%s" % srcdir]
            default_flags = []

        default_flags.append("-D_GLIBCXX_ASSERT")
        if fnmatch.fnmatch(context["DejaGNUTest.target"],
                           "powerpc-*-darwin*"):
            default_flags += ["-multiply_defined", "suppress"]
        context["V3Init.basic_cxx_flags"] = basic_flags
        context["V3Init.default_cxx_flags"] = default_flags
        
        if standalone:
            # Build libv3test.a.
            makefile_in = open(os.path.join(standalone_root,
                                            "qm-misc",
                                            "util-Makefile"))
            makefile_str = makefile_in.read()
            makefile_str = makefile_str.replace("@ROOT@",
                                                standalone_root)
            makefile_str = makefile_str.replace("@CXX@",
                                                compiler.GetPath())
            flags = compiler.GetOptions() + basic_flags
            makefile_str = makefile_str.replace("@CXXFLAGS@",
                                                " ".join(flags))
            makefile_out = open(os.path.join(outdir, "Makefile"), "w")
            makefile_out.write(makefile_str)
            makefile_out.close()
            
            make_executable = RedirectedExecutable()
            make_command = ["make", "libv3test.a"]
            status = make_executable.Run(make_command, dir=outdir)
            if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
                result.SetOutcome(result.ERROR,
                                  "Error building libv3test.a",
                                  {"status": str(status),
                                   "stdout": "<pre>"
                                             + make_executable.stdout
                                             + "</pre>",
                                   "stderr": "<pre>"
                                             + make_executable.stderr
                                             + "</pre>",
                                   "command": " ".join(make_command),
                                   })
                return

        
    def _CalcBuildTreeFlags(self, result, context, blddir, compiler):
        """This function emulates a bit of normal.exp and a bit of
        v3-init."""

        basic_flags = []
        default_flags = []

        # Find the command to use.
        for subdir in "", "scripts":
            command = os.path.join(blddir, subdir, "testsuite_flags")
            if os.path.isfile(command):
                break

        result["V3Init.testsuite_flags_command"] = \
            "<pre>" + command + "</pre>"

        executable = RedirectedExecutable()
        executable.Run([command, "--cxxflags"])
        basic_flags += executable.stdout.split()
        executable.Run([command, "--build-includes"])
        basic_flags += executable.stdout.split()

        # 'normal.exp' checks for the existence of 'testsuite_flags' and
        # pretends the output is "" if it doesn't exist; we simply
        # assume it always exists.
        executable.Run([command, "--cxxpchflags"])
        if executable.stdout.find("sage:") != -1:
            # This 'testsuite_flags' does not support --cxxpchflags.
            pass
        else:
            default_flags += executable.stdout.split()

        return (basic_flags, default_flags)

# dg-runtest calls dg-test calls "libstdc++-dg-test prog do_what
# DEFAULT_CXXFLAGS" (DEFAULT_CXXFLAGS as in normal.exp)
# Which calls
#   v3_target_compile $prog $output_file $compile_type additional_flags=$DEFAULT_CXXFLAGS
# Which sets cxx_final to "$cxx [libgloss_link_flags] $cxxflags $includes"
# then calls
#   target_compile $prog $output_file $compile_type additional_flags=$DEFAULT_CXXFLAGS,compiler=$cxx_final,ldflags=-L$blddir/testsuite,libs=-lv3test
# for us, libgloss doesn't exist, which simplifies things.

class V3DGTest(DGTest, GCCTestBase):
    """A 'V3DGTest' is a libstdc++-v3 test using the 'dg' driver.

    This test class emulates the 'lib/libstdc++.exp' and 'lib/prune.exp
    and 'libstdc++-dg/normal.exp' source files in the libstdc++-v3
    testsuite."""

    _default_kind = DGTest.KIND_RUN

    _language = "cplusplus"

    _libdir_context_property = "V3Init.libpaths"

    def Run(self, context, result):

        self._SetUp(context)
        self._RunDGTest(context["V3Init.basic_cxx_flags"],
                        context["V3Init.default_cxx_flags"],
                        context,
                        result)
        

    def _PruneOutput(self, output):
        """This method emulates 'prune.exp'."""

        # Prune out Cygwin warnings and parts of warnings that refer to
        # location of previous definitions etc.
        output = re.sub(r"(^|\n)[^\n]*: -ffunction-sections may affect "
                        r"debugging on some targets[^\n]",
                        "", output)
        output = re.sub(r"(^|\n)[^\n]*: In function [^\n]*", "", output)
        return output


    def _GetTargetEnvironment(self, context):

        env = {}
        for name in _ld_library_path_names:
            env[name] = context["V3Init.ld_library_path"]
        return env


    def _RunTargetExecutable(self, context, result, file, dir = None):

        if dir is None:
            dir = context["V3Init.outdir"]

        sup = super(V3DGTest, self)
        return sup._RunTargetExecutable(context, result, file, dir)


    def _RunTool(self, path, kind, options, context, result):
        """This method emulates libstdc++-dg-test."""

        source_files = [path]
        
        file = self._GetOutputFile(context, kind, path)
        kind = self._test_kind_map[kind]

        if kind == GCCTestBase.KIND_EXECUTABLE:
            source_files += ["-lv3test"]

        output = self._Compile(context, result, source_files, file,
                               kind, options)
        return (output, file)


    def _GetOutputFile(self, context, kind, path):

        base = os.path.basename(path)
        if kind != self.KIND_PRECOMPILE:
            base = os.path.splitext(base)[0]
        base += { DGTest.KIND_PREPROCESS : ".i",
                  DGTest.KIND_COMPILE : ".s",
                  DGTest.KIND_ASSEMBLE : ".o",
                  DGTest.KIND_LINK: ".exe",
                  DGTest.KIND_RUN : ".exe",
                  GCCTestBase.KIND_PRECOMPILE : ".gch",
                  }[kind]

        return os.path.join(context.GetTemporaryDirectory(), base)


    def _DGrequire_iconv(self, line_num, args, context):
        """Emulate the 'dg-require-iconv' command.

        Emulates code from 'libstdc++-v3/testsuite/lib/dg-options.exp'
        and 'gcc/testsuite/lib/target-supports.exp'.
        
        'line_num' -- The number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""

        # Parse arguments.
        if len(args) != 1:
            self._Error("dg-require-iconv: wrong number of arguments")
            return

        charset = args[0]

        # Check to see if iconv does exist and work.
        # First by creating and compiling a test program...
        tmpdir = context.GetTemporaryDirectory()
        tmpc = os.path.join(tmpdir, "tmp.c")
        tmpx = os.path.join(tmpdir, "tmp.x")
        f = open(tmpc, "w")
        f.write("""\
#include <iconv.h>
int main (void)
{
    iconv_t cd;
    cd = iconv_open("%(charset)s", "UTF-8");
    if (cd == (iconv_t) -1)
        return 1;
    return 0;
}
"""
                % {"charset": charset})
        f.close()

        compiler = context["CompilerTable.compiler_table"][self._language]
        options = []

        options += context["V3Init.basic_cxx_flags"]
        options += context["V3Init.default_cxx_flags"]
        libpaths = context["V3Init.libpaths"]
        options += ["-L" + p for p in libpaths]

        if context.has_key("GCCTest.libiconv"):
            libiconv_opts = context["GCCTest.libiconv"].split()
        else:
            libiconv_opts = []
        
        (status, output) = compiler.Compile(compiler.MODE_LINK,
                                            [tmpc] + libiconv_opts,
                                            tmpdir, options, tmpx)
        if output == "":
            # ...and then running it, if there are no errors.
            executable = self.TargetExecutable(self.executable_timeout)
            command = [tmpx]
            environment = self._GetTargetEnvironment(context)
            status = executable.Run(command, environment, tmpdir)
            if os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0:
                # We have working libiconv.  Continue as normal.
                return

        # Something went wrong somewhere -- libiconv is not available.
        # Turn off the test.
        self._selected = 0
        # Not clear that setting the expectation here serves any
        # purpose, but it's what 'dg-options.exp' does, so we do too.
        self._expectation = Result.PASS



# check-abi first builds
#    abi_check
#    baseline_symbols
#    current_symbols.txt
# then does
#    ./abi_check --check(-verbose) ./current_symbols.txt ${baseline_file}
#
# abi_check is built by automake as a program.
# baseline_symbols just checks to see if a baseline file exists
# current_symbols.txt depends on ${extract_symvers} ../src/.libs/libstdc++.so
#
#
# new-abi-baseline is what actually generates a new baseline.
# it does it with ${extract_symvers} ../src/.libs/libstdc++.so ${baseline_file}
# baseline_file = ${baseline_dir}/baseline_symbols.txt
# baseline_dir is set by autoconf to some mad thing...
#    $glibcxx_srcdir/config/abi/${abi_baseline_pair}\$(MULTISUBDIR)"
# abi_baseline_pair is set by autoconf to host_cpu-host_os by default.
# but there are some special cases, in particular:
#    x86_64-*-linux*     -> x86_64-linux-gnu
#    alpha*-*-freebsd5*  -> alpha-freebsd5
#    i*86-*-freebsd4*    -> i386-freebsd4
#    i*86-*-freebsd5*    -> i386-freebsd5
#    sparc*-*-freebsd5*  -> sparc-freebsd5
#
# extract_symvers = $(glibcxx_srcdir)/scripts/extract_symvers
# extract_symvers is actually just a shell script
        
class V3ABITest(Test):
    """A 'V3ABITest' checks the ABI of libstdc++ against a baseline.

    Depends on context variable 'V3Test.abi_baseline_file'."""

    def Run(self, context, result):

        # Some variables we'll need throughout.
        executable = RedirectedExecutable()
        tmpdir = context.GetTemporaryDirectory()
        outdir = context["V3Init.outdir"]
        srcdir = self.GetDatabase().GetRoot()

        # First we make sure that the abi_check program exists.
        abi_check = os.path.join(outdir, "abi_check")
        status = executable.Run(["make", "abi_check"], dir=outdir)
        result["make_abi_check_stdout"] = ("<pre>" + executable.stdout
                                           + "</pre>")
        result["make_abi_check_stderr"] = ("<pre>" + executable.stderr
                                           + "</pre>")
        result["make_abi_check_status"] = str(status)
        if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
            result.SetOutcome(result.ERROR, "Error building abi_check")
            return
        if not os.path.isfile(abi_check):
            result.SetOutcome(result.ERROR,
                              "No abi_check program '%s'" % abi_check)
            return

        # Now make sure the baseline file exists.
        baseline_type = self._GetAbiName(context["DejaGNUTest.target"])
        baseline_file = os.path.join(srcdir, "..", "config", "abi",
                                     baseline_type,
                                     "baseline_symbols.txt")
        result["baseline_file"] = baseline_file
        if not os.path.isfile(baseline_file):
            result.SetOutcome(result.ERROR,
                              "No baseline file '%s'" % baseline_file)
            return

        # Check that we have the 'extract_symvers' script.
        # 3.4+ stores it in scripts; 3.3 stores it in config/abi.
        subdirs = ["scripts", os.path.join("config", "abi")]
        for subdir in subdirs:
            extract_symvers = os.path.join(srcdir, "..",
                                           subdir,
                                           "extract_symvers")
            if os.path.isfile(extract_symvers):
                break
        else:
            result.SetOutcome(result.ERROR,
                              "Can't find extract_symvers")
            return

        # Extract the current symbols.
        # First use ldd to find the libstdc++ in use.
        status = executable.Run(["ldd", "abi_check"], dir=outdir)
        result["ldd_stdout"] = ("<pre>" + executable.stdout
                                            + "</pre>")
        result["ldd_stderr"] = ("<pre>" + executable.stderr
                                            + "</pre>")
        result["ldd_status"] = str(status)
        if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
            result.SetOutcome(result.ERROR,
                              "Error running ldd to find libstdc++")
            return
        for token in executable.stdout.split():
            if os.sep in token and token.find("libstdc++") != -1:
                libstdcpp = token
                break
        else:
            result.SetOutcome(result.ERROR,
                              "Could not find path to libstdc++ in "
                              "ldd output")
            return
#         libstdcpp = os.path.join(outdir, "..", "src", ".libs",
#                                  "libstdc++.so")
        result["libstdcpp_path"] = libstdcpp

        curr_symbols = os.path.join(tmpdir, "current_symbols.txt")
        status = executable.Run([extract_symvers,
                                 libstdcpp,
                                 curr_symbols])
        result["extract_symvers_stdout"] = ("<pre>" + executable.stdout
                                            + "</pre>")
        result["extract_symvers_stderr"] = ("<pre>" + executable.stderr
                                            + "</pre>")
        result["extract_symvers_status"] = str(status)
        if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
            result.SetOutcome(result.ERROR, "Error extracting symbols")
            return
        if not os.path.isfile(curr_symbols):
            result.SetOutcome(result.ERROR, "No symbols extracted")
            return

        # We have the checker program, we have the baseline, we have the
        # current symbols.  Now we use the former to compare the
        # latter.
        status = executable.Run([abi_check, "--check-verbose",
                                 curr_symbols, baseline_file])
        result["comparison_stdout"] = ("<pre>" + executable.stdout
                                            + "</pre>")
        result["comparison_stderr"] = ("<pre>" + executable.stderr
                                            + "</pre>")
        result["comparison_status"] = str(status)
        if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
            result.SetOutcome(result.ERROR,
                              "Error comparing symbols to baseline")
            return

        # Parse the output.
        for line in executable.stdout.split("\n"):
            if line.startswith("# of "):
                num_changes_str = line.split(":", 1)[1].strip()
                num_changes = int(num_changes_str)
                if num_changes != 0:
                    result.Fail("Changes against ABI baseline detected")
                    result["failing_line"] = line.strip()
                    return


    def _GetAbiName(self, host):
        """Map a target triple to a abi directory name.

        Emulates 'configure.host'."""

        cpu, vendor, os = host.split("-", 2)
        m = fnmatch.fnmatch
        if m(cpu, "alpha*"):
            cpu = "alpha"
        elif m(cpu, "i[567]86") or m(cpu, "x86_64"):
            cpu = "i486"
        elif m(cpu, "hppa*"):
            cpu = "hppa"
        elif m(cpu, "powerpc*") or m(cpu, "rs6000"):
            cpu = "powerpc"
        elif m(cpu, "s390x"):
            cpu = "s390"
        elif m(cpu, "sparc*") or m(cpu, "ultrasparc"):
            cpu = "sparc"

        return "%s-%s" % (cpu, os)
            
