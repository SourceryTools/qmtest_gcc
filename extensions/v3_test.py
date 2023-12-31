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

class V3Base(object):
    """Methods required by all V3 classes."""

    def _HaveCompiler(self, context):
        """Returns true if we have a compiler."""

        if not context.has_key("V3Test.have_compiler"):
            # By default we assume there is a compiler.
            return True
        
        # But if there is a context key, we trust it.
        return qm.parse_boolean(context["V3Test.have_compiler"])



class V3Init(Resource, V3Base):
    """All V3 tests depend on one of these for setup."""

    def SetUp(self, context, result):

        # Get general information that will be used through the rest of
        # the setup.
        srcdir = self.GetDatabase().GetRoot()
        target = context["DejaGNUTest.target"]

        # If there is a compiler output directory given, ensure the path
        # is absolute, and ensure it exists.
        if context.has_key("V3Test.compiler_output_dir"):
            compiler_outdir = context["V3Test.compiler_output_dir"]
            compiler_outdir = os.path.abspath(compiler_outdir)
            context["V3Test.compiler_output_dir"] = compiler_outdir
            if not os.path.exists(compiler_outdir):
                os.mkdir(compiler_outdir)
        else:
            compiler_outdir = None
                
        if not self._HaveCompiler(context) and compiler_outdir is None:
            result.SetOutcome(result.ERROR,
                              "If have_compiler is false, then "
                              "V3Test.compiler_output_dir must be "
                              "provided")
            return

        # Are we using the standalone testsuite to test an installed
        # libstdc++/g++, or the integrated testsuite to test a
        # just-built libstdc++/g++?  Check for the magic file that the
        # standalone package contains.
        standalone_marker = os.path.join(srcdir, "..",
                                         "THIS-IS-STANDALONE-V3")
        standalone = os.path.exists(standalone_marker)
        if standalone:
            standalone_root = os.path.join(srcdir, "..")
        context["V3Test.is_standalone"] = standalone

        # Find the compiler.
        if self._HaveCompiler(context):
            compilers = context["CompilerTable.compilers"]
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
            if context.has_key("V3Test.outdir"):
                result.SetOutcome(result.ERROR,
                                  "Set V3Test.scratch_dir, not outdir")
                return
            outdir = context["V3Test.scratch_dir"]
            outdir = os.path.abspath(outdir)
            if not os.path.exists(outdir):
                os.mkdir(outdir)
            
        context["V3Test.outdir"] = outdir

        # Ensure that the message format files are available.
        # This requires different commands depending on whether we're
        # using the gcc build system or not.
        if not standalone:
            locale_dir = os.path.join(blddir, "po")
            make_command = ["make", "-j1", "check"]
        else:
            if self._HaveCompiler(context):
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
                makefile_out = open(os.path.join(locale_dir,
                                                 "Makefile"),
                                    "w")
                makefile_out.write(makefile_str)
                makefile_out.close()
                make_command = ["make", "-j1", "locales"]
            else:
                # We're standalone without a compiler; we'll use the
                # locale dir in the compiler output directory directly.
                locale_dir = os.path.join(compiler_outdir, "qm_locale")
            # Either way, we need to provide the locale directory as an
            # environment variable, _not_ as a #define.
            context["V3Init.env_V3_LOCALEDIR"] = locale_dir

        # Now do the actual compiling, if possible.
        if self._HaveCompiler(context):
            make_executable = RedirectedExecutable()
            status = make_executable.Run(make_command, dir=locale_dir)
            if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
                q_stdout = result.Quote(make_executable.stdout)
                q_stderr = result.Quote(make_executable.stderr)
                result.SetOutcome(result.ERROR,
                                  "Error building locale information",
                                  {"status": str(status),
                                   "stdout": q_stdout,
                                   "stderr": q_stderr,
                                   "command": " ".join(make_command),
                                   })
                return

            if compiler_outdir is not None:
                co_ld = os.path.join(compiler_outdir, "qm_locale")
                if os.path.exists(co_ld):
                    shutil.rmtree(co_ld, ignore_errors=True)
                shutil.copytree(locale_dir, co_ld)
            

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
        context["V3Test.libpaths"] = libpaths
        context["V3Test.ld_library_path"] = ld_library_path
        result["V3Test.ld_library_path"] = ld_library_path

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
            # doesn't seem to hurt.  Only exception is that we
            # purposefully leave out -DLOCALEDIR when doing standalone
            # testing, so that it will be picked up from the environment
            # instead.  This ensures that binary-only tests can be moved
            # after being compiled.
            basic_flags = [# v3.4 only:
                           "-D_GLIBCXX_ASSERT",
                           # v3.3 only:
                           "-DDEBUG_ASSERT",
                           # Common:
                           "-g", "-O2",
                           "-ffunction-sections", "-fdata-sections",
                           "-fmessage-length=0",
                           "-I%s" % srcdir]
            default_flags = []
            

        default_flags.append("-D_GLIBCXX_ASSERT")
        if fnmatch.fnmatch(context["DejaGNUTest.target"],
                           "powerpc-*-darwin*"):
            default_flags += ["-multiply_defined", "suppress"]
        context["V3Test.basic_cxx_flags"] = basic_flags
        context["V3Test.default_cxx_flags"] = default_flags
        
        if standalone:
            # Ensure libv3test.a exists in 'outdir'.
            if self._HaveCompiler(context):
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
                makefile_out = open(os.path.join(outdir, "Makefile"),
                                    "w")
                makefile_out.write(makefile_str)
                makefile_out.close()

                make_executable = RedirectedExecutable()
                make_command = ["make", "libv3test.a"]
                status = make_executable.Run(make_command, dir=outdir)
                if (not os.WIFEXITED(status)
                    or os.WEXITSTATUS(status) != 0):
                    q_stdout = result.Quote(make_executable.stdout)
                    q_stderr = result.Quote(make_executable.stderr)
                    command_str = " ".join(make_command),
                    result.SetOutcome(result.ERROR,
                                      "Error building libv3test.a",
                                      {"status": str(status),
                                       "stdout": q_stdout,
                                       "stderr": q_stderr,
                                       "command": command_str,
                                       })
                    return

                # If we have an compiler output dir, use it.
                if compiler_outdir is not None:
                    shutil.copy(os.path.join(outdir, "libv3test.a"),
                                os.path.join(compiler_outdir,
                                             "libv3test.a"))
            else:
                # No compiler, so we just copy it out of the compiler
                # output dir.
                shutil.copy(os.path.join(compiler_outdir,
                                         "libv3test.a"),
                            os.path.join(outdir, "libv3test.a"))

        
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

        result["V3Test.testsuite_flags_command"] = result.Quote(command)

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

# How DejaGNU does this, for reference:
#
# dg-runtest calls dg-test calls "libstdc++-dg-test prog do_what
# DEFAULT_CXXFLAGS" (DEFAULT_CXXFLAGS as in normal.exp)
# Which calls
#   v3_target_compile $prog $output_file $compile_type additional_flags=$DEFAULT_CXXFLAGS
# Which sets cxx_final to "$cxx [libgloss_link_flags] $cxxflags $includes"
# then calls
#   target_compile $prog $output_file $compile_type additional_flags=$DEFAULT_CXXFLAGS,compiler=$cxx_final,ldflags=-L$blddir/testsuite,libs=-lv3test
# for us, libgloss doesn't exist, which simplifies things.

class V3DGTest(DGTest, GCCTestBase, V3Base):
    """A 'V3DGTest' is a libstdc++-v3 test using the 'dg' driver.

    This test class emulates the 'lib/libstdc++.exp' and 'lib/prune.exp
    and 'libstdc++-dg/normal.exp' source files in the libstdc++-v3
    testsuite."""

    _default_kind = DGTest.KIND_RUN

    _language = "cplusplus"

    _libdir_context_property = "V3Test.libpaths"

    def Run(self, context, result):

        self._SetUp(context)

        if context.has_key("V3Test.compiler_output_dir"):
            # When using a special output directory, we always save the
            # executables.
            keep_output = 1
        else:
            keep_output = 0
        self._RunDGTest(context["V3Test.basic_cxx_flags"],
                        context["V3Test.default_cxx_flags"],
                        context,
                        result,
                        keep_output=keep_output)
        

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
            env[name] = context["V3Test.ld_library_path"]
        if context.has_key("V3Init.env_V3_LOCALEDIR"):
            env["V3_LOCALEDIR"] = context["V3Init.env_V3_LOCALEDIR"]
        return env


    def _RunTargetExecutable(self, context, result, file, dir = None):

        if dir is None:
            dir = context["V3Test.outdir"]

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


    def _RunDGToolPortion(self, path, tool_flags, context, result):
        """Don't run the compiler if in pre-compiled mode."""

        if not self._HaveCompiler(context):
            # Don't run the compiler, just pretend we did.
            return self._GetOutputFile(context, self._kind, path)
            
        return super(V3DGTest, self)._RunDGToolPortion(path, tool_flags,
                                                       context, result)
            

    def _RunDGExecutePortion(self, file, context, result):
        """Emit an UNTESTED result if not compiling and not running."""

        if (not self._HaveCompiler(context)
            and self._kind != DGTest.KIND_RUN):
            # We didn't run the compiler, and we're not going to run the
            # executable; we'd better emit something here because we're
            # not doing it anywhere else.
            result["V3DGTest.explanation_1"] = (
                "This is a compiler test, and we are running in no "
                "compiler mode.  Skipped.")
            # Magic marker for the TET output stream to pick up on:
            result["test_not_relevant_to_testing_mode"] = "true"
            self._RecordDejaGNUOutcome(result,
                                       self.UNTESTED, self._name)
            return
                
        super(V3DGTest, self)._RunDGExecutePortion(file,
                                                   context, result)


    def _GetOutputFile(self, context, kind, path):

        if context.has_key("V3Test.compiler_output_dir"):
            dir = context["V3Test.compiler_output_dir"]
            srcdir = self.GetDatabase().GetRoot()
            path = os.path.normpath(path)
            srcdir = os.path.normpath(srcdir)
            assert path.startswith(srcdir)
            base = path[len(srcdir):]
            base = base.replace("/", "_")
        else:
            dir = context.GetTemporaryDirectory()
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

        return os.path.join(dir, base)


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

        # First check to see if we have a compiler.  We can't do
        # anything useful without one.
        if not self._HaveCompiler(context):
            # No compiler; we'll go ahead and hope for the best.
            # Better would be to save the test programs to the output
            # directory, but this is difficult; on the other hand, not
            # doing so may cause spurious failures if a character set is
            # not in fact supported by our local libiconv...
            return

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

        compiler = context["CompilerTable.compilers"][self._language]
        options = []

        options += context["V3Test.basic_cxx_flags"]
        options += context["V3Test.default_cxx_flags"]
        libpaths = context["V3Test.libpaths"]
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
            host = context['CompilerTable.target']
            environment = self._GetTargetEnvironment(context)
            status, output = host.Run(tmpx, environment, tmpdir)
            if os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0:
                # We have working libiconv.  Continue as normal.
                return

        # Something went wrong somewhere -- libiconv is not available.
        # Turn off the test.
        self._selected = 0
        # Not clear that setting the expectation here serves any
        # purpose, but it's what 'dg-options.exp' does, so we do too.
        self._expectation = Result.PASS



# How the real GCC tree does things:
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
# It does it with ${extract_symvers} ../src/.libs/libstdc++.so ${baseline_file}
# baseline_file = ${baseline_dir}/baseline_symbols.txt
# baseline_dir is set by autoconf to some mad thing...
#    $glibcxx_srcdir/config/abi/${abi_baseline_pair}\$(MULTISUBDIR)"
# abi_baseline_pair is set by autoconf to host_cpu-host_os by default.
# But there are some special cases.
#
# extract_symvers = $(glibcxx_srcdir)/scripts/extract_symvers
# extract_symvers is actually just a shell script; we don't need to
# compile it.
        
class V3ABITest(Test, V3Base):
    """A 'V3ABITest' checks the ABI of libstdc++ against a baseline.

    Depends on context variable 'V3Test.abi_baseline_file'."""

    def Run(self, context, result):

        # Some variables we'll need throughout.
        executable = RedirectedExecutable()
        tmpdir = context.GetTemporaryDirectory()
        outdir = context["V3Test.outdir"]
        srcdir = self.GetDatabase().GetRoot()
        if context.has_key("V3Test.compiler_output_dir"):
            compiler_outdir = context["V3Test.compiler_output_dir"]
        else:
            compiler_outdir = None

        # First we make sure that the abi_check program exists.
        if not self._HaveCompiler(context):
            # If we have no compiler, we must find it in the compiler
            # output dir.
            if compiler_outdir is None:
                result.SetOutcome(result.ERROR,
                                  "No compiler output dir, "
                                  "but no compiler either.")
                return
            abi_check = os.path.join(compiler_outdir, "abi_check")
        else:
            # Otherwise, we have to try building it.
            abi_check = os.path.join(outdir, "abi_check")
            status = executable.Run(["make", "abi_check"], dir=outdir)
            quote = result.Quote
            result["make_abi_check_stdout"] = quote(executable.stdout)
            result["make_abi_check_stderr"] = quote(executable.stderr)
            result["make_abi_check_status"] = str(status)
            if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
                result.SetOutcome(result.ERROR,
                                  "Error building abi_check")
                return
            # Ensure that the abi_check program does end up in the
            # compiler output dir, if necessary.
            if compiler_outdir is not None:
                shutil.copy(abi_check,
                            os.path.join(compiler_outdir, "abi_check"))
        
        if not os.path.isfile(abi_check):
            result.SetOutcome(result.ERROR,
                              "No abi_check program '%s'"
                              % abi_check)
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
        # First use ldd to find the libstdc++ in use.  'abi_check' is a
        # handy C++ program; we'll check which library it's linked
        # against.
        status = executable.Run(["ldd", abi_check], dir=outdir)
        result["ldd_stdout"] = result.Quote(executable.stdout)
        result["ldd_stderr"] = result.Quote(executable.stderr)
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
        result["libstdcpp_path"] = libstdcpp

        curr_symbols = os.path.join(tmpdir, "current_symbols.txt")
        status = executable.Run([extract_symvers,
                                 libstdcpp,
                                 curr_symbols])
        quote = result.Quote
        result["extract_symvers_stdout"] = quote(executable.stdout)
        result["extract_symvers_stderr"] = quote(executable.stderr)
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
        quote = result.Quote
        result["comparison_stdout"] = quote(executable.stdout)
        result["comparison_stderr"] = quote(executable.stderr)
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

        m = fnmatch.fnmatch

        # Special cases:
        if m(host, "x86_64-*-linux*"):
            return "x86_64-linux-gnu"
        elif m(host, "alpha*-*-freebsd5*"):
            return "alpha-freebsd5"
        elif m(host, "i*86-*-freebsd4*"):
            return "i386-freebsd4"
        elif m(host, "i*86-*-freebsd5*"):
            return "i386-freebsd5"
        elif m(host, "sparc*-*-freebsd5*"):
            return "sparc-freebsd5"

        cpu, vendor, os = host.split("-", 2)
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
