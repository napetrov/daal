load("@onedal//dev/bazel:release.bzl",
    "release",
    "release_include",
)

# Example source files
filegroup(
    name = "examples_cpp",
    srcs = glob([
        "examples/daal/cpp/source/**/*.cpp",
        "examples/daal/cpp/source/**/*.h",
        "examples/oneapi/cpp/source/**/*.cpp",
        "examples/oneapi/cpp/source/**/*.hpp",
        "examples/oneapi/dpc/source/**/*.cpp",
        "examples/oneapi/dpc/source/**/*.hpp",
    ]),
)

# Example data files
filegroup(
    name = "examples_data",
    srcs = glob([
        "examples/daal/data/**/*.csv",
        "examples/oneapi/data/**/*.csv",
    ]),
)

# Environment scripts
filegroup(
    name = "env_scripts",
    srcs = [
        "deploy/local/vars_lnx.sh",
        "deploy/local/vars_mac.sh",
        "deploy/local/vars_win.bat",
    ],
)

release(
    name = "release",
    include = [
        release_include(
            hdrs = [ "@onedal//cpp/daal:public_includes" ],
            skip_prefix = "cpp/daal/include",
        ),
        release_include(
            hdrs = [ "@onedal//cpp/daal:kernel_defines" ],
            add_prefix = "services/internal",
        ),
        release_include(
            hdrs = [ "@onedal//cpp/oneapi/dal:public_includes" ],
            skip_prefix = "cpp",
        ),
    ],
    lib = [
        "@onedal//cpp/daal:core_static",
        "@onedal//cpp/daal:thread_static",
        "@onedal//cpp/daal:core_dynamic",
        "@onedal//cpp/daal:thread_dynamic",
        "@onedal//cpp/oneapi/dal:static",
        "@onedal//cpp/oneapi/dal:dynamic",
        "@onedal//cpp/oneapi/dal:static_parameters",
        "@onedal//cpp/oneapi/dal:dynamic_parameters",
    ] + select({
        "@config//:release_dpc_enabled": [
            "@onedal//cpp/oneapi/dal:static_dpc",
            "@onedal//cpp/oneapi/dal:dynamic_dpc",
            "@onedal//cpp/oneapi/dal:static_parameters_dpc",
            "@onedal//cpp/oneapi/dal:dynamic_parameters_dpc",
        ],
        "//conditions:default": [],
    }),
    examples = [":examples_cpp"],
    data_files = [":examples_data"],
    env_scripts = [":env_scripts"],
    pkgconfig_template = "deploy/pkg-config/pkg-config.tpl",
    cmake_template = "cmake/templates/oneDALConfig.cmake.in",
)
