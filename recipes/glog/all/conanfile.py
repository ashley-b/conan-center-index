from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import copy, get, rmdir
from conan.tools.scm import Version
from conan.tools.build import check_min_cppstd
import os

required_conan_version = ">=1.54.0"


class GlogConan(ConanFile):
    name = "glog"
    description = "Google logging library"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/google/glog/"
    topics = ("logging",)
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_gflags": [True, False],
        "with_threads": [True, False],
        "with_unwind": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_gflags": True,
        "with_threads": True,
        "with_unwind": True,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.os not in ["Linux", "FreeBSD"]:
            del self.options.with_unwind

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if self.options.with_gflags:
            self.options["gflags"].shared = self.options.shared

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_gflags:
            self.requires("gflags/2.2.2", transitive_headers=True, transitive_libs=True)
        # 0.4.0 requires libunwind unconditionally
        if self.options.get_safe("with_unwind"):
            self.requires("libunwind/1.8.0", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if Version(self.version) < "0.7.0":
            return

        check_min_cppstd(self, 14)

    def build_requirements(self):
        if Version(self.version) >= "0.7.0":
            self.tool_requires("cmake/[>=3.22 <4]")
        elif Version(self.version) >= "0.6.0":
            self.tool_requires("cmake/[>=3.16 <4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = VirtualBuildEnv(self)
        tc.generate()

        tc = CMakeToolchain(self)
        tc.variables["WITH_GFLAGS"] = self.options.with_gflags
        tc.variables["WITH_THREADS"] = self.options.with_threads
        tc.variables["WITH_PKGCONFIG"] = True
        if self.settings.os == "Emscripten":
            tc.variables["WITH_SYMBOLIZE"] = False
            tc.variables["HAVE_SYSCALL_H"] = False
            tc.variables["HAVE_SYS_SYSCALL_H"] = False
        else:
            tc.variables["WITH_SYMBOLIZE"] = True
        tc.variables["WITH_UNWIND"] = self.options.get_safe("with_unwind", default=False)
        tc.variables["BUILD_TESTING"] = False
        tc.variables["WITH_GTEST"] = False
        # TODO: Remove after fixing https://github.com/conan-io/conan/issues/12012
        # Needed for https://github.com/google/glog/blob/v0.7.1/CMakeLists.txt#L81
        # and https://github.com/google/glog/blob/v0.7.1/CMakeLists.txt#L90
        tc.variables["CMAKE_TRY_COMPILE_CONFIGURATION"] = str(self.settings.build_type)
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "glog")
        self.cpp_info.set_property("cmake_target_name", "glog::glog")
        self.cpp_info.set_property("pkg_config_name", "libglog")
        postfix = "d" if self.settings.build_type == "Debug" else ""
        self.cpp_info.libs = ["glog" + postfix]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = ["dbghelp"]
            self.cpp_info.defines = ["GLOG_NO_ABBREVIATED_SEVERITIES"]
            decl = "__declspec(dllimport)" if self.options.shared else ""
            self.cpp_info.defines.append(f"GOOGLE_GLOG_DLL_DECL={decl}")
        if self.options.with_gflags and not self.options.shared:
            self.cpp_info.defines.extend(["GFLAGS_DLL_DECLARE_FLAG=", "GFLAGS_DLL_DEFINE_FLAG="])
        if Version(self.version) >= "0.7.0":
            self.cpp_info.defines.extend(["GLOG_USE_GLOG_EXPORT="])
