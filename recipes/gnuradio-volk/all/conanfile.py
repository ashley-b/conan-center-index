from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rmdir

import os

required_conan_version = ">=1.53.0"


class GnuradioVolkConan(ConanFile):
    name = "gnuradio-volk"
    license = "LGPL-3.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://libvolk.org/"
    topics = ("simd", "sdr", "simd-programming", "simd-instructions")
    package_type = "library"
    description = (
        "The Vector Optimized Library of Kernels"
    )
    #python_requires = "mako/[>=0.4.2]"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_cpu_features": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_cpu_features": True
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_cpu_features:
            self.requires("cpu_features/0.8.0")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], destination=self.source_folder, strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["VOLK_CPU_FEATURES"] = self.options.with_cpu_features
        tc.variables["ENABLE_ORC"] = False
        tc.variables["ENABLE_TESTING"] = False
        tc.variables["ENABLE_PROFILING"] = False
        tc.variables["ENABLE_MODTOOL"] = False
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.libs = ["volk"]
        self.cpp_info.set_property("cmake_file_name", "Volk")
        self.cpp_info.set_property("cmake_target_name", "volk::volk")
        self.cpp_info.set_property("pkg_config_name", "volk")

