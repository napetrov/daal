#===============================================================================
# Copyright 2020 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

load("@onedal//dev/bazel:utils.bzl", "utils", "paths")
load("@onedal//dev/bazel:cc.bzl", "ModuleInfo")

def _match_file_name(file, entries):
    for entry in entries:
        if entry in file.path:
            return True
    return False

def _collect_headers(dep):
    headers = []
    if ModuleInfo in dep:
        headers += dep[ModuleInfo].compilation_context.headers.to_list()
    elif CcInfo in dep:
        headers += dep[CcInfo].compilation_context.headers.to_list()
    elif DefaultInfo in dep:
        headers += dep[DefaultInfo].files.to_list()
    return utils.unique_files(headers)

def _collect_default_files(deps):
    files = []
    for dep in deps:
        if DefaultInfo in dep:
            files += dep[DefaultInfo].files.to_list()
    return utils.unique_files(files)

def _copy(ctx, src_file, dst_path):
    # TODO: Use extra toolchain
    dst_file = ctx.actions.declare_file(dst_path)
    ctx.actions.run(
        executable = "cp",
        inputs = [ src_file ],
        outputs = [ dst_file ],
        use_default_shell_env = True,
        arguments = [ src_file.path, dst_file.path ],
    )
    return dst_file

def _try_relativize(path, start):
    if path.startswith(start):
        return paths.relativize(path, start)
    return path

def _copy_include(ctx, prefix):
    include_prefix = paths.join(prefix, "include")
    dst_files = []
    for include, prefix, skip_prefix in zip(ctx.attr.include, ctx.attr.include_prefix,
                                            ctx.attr.include_skip_prefix):
        headers = _collect_headers(include)
        for header in headers:
            if skip_prefix:
                dst_path = _try_relativize(header.path, skip_prefix)
            elif prefix:
                dst_path = paths.join(prefix, header.basename)
            dst_file = _copy(ctx, header, paths.join(include_prefix, dst_path))
            dst_files.append(dst_file)
    return dst_files

def _copy_lib(ctx, prefix):
    lib_prefix = paths.join(prefix, "lib", "intel64")
    libs = _collect_default_files(ctx.attr.lib)
    dst_files = []
    for lib in libs:
        dst_path = paths.join(lib_prefix, lib.basename)
        dst_file = _copy(ctx, lib, dst_path)
        dst_files.append(dst_file)
    return dst_files

def _copy_examples(ctx, prefix):
    examples_prefix = paths.join(prefix, "examples")
    examples = _collect_default_files(ctx.attr.examples)
    dst_files = []
    for example in examples:
        # Preserve directory structure for examples
        dst_path = paths.join(examples_prefix, example.basename)
        dst_file = _copy(ctx, example, dst_path)
        dst_files.append(dst_file)
    return dst_files

def _copy_data_files(ctx, prefix):
    data_prefix = paths.join(prefix, "examples", "data")
    data_files = _collect_default_files(ctx.attr.data_files)
    dst_files = []
    for data_file in data_files:
        # Preserve directory structure for data files
        dst_path = paths.join(data_prefix, data_file.basename)
        dst_file = _copy(ctx, data_file, dst_path)
        dst_files.append(dst_file)
    return dst_files

def _copy_env_scripts(ctx, prefix):
    """Copy environment scripts from deploy/local folder"""
    env_prefix = paths.join(prefix, "env")
    env_scripts = _collect_default_files(ctx.attr.env_scripts)
    dst_files = []
    for env_script in env_scripts:
        dst_path = paths.join(env_prefix, env_script.basename)
        dst_file = _copy(ctx, env_script, dst_path)
        dst_files.append(dst_file)
    return dst_files

def _generate_pkgconfig_files(ctx, prefix):
    """Generate PKG-CONFIG files using the template and Python script logic"""
    # Read template file
    template_content = ctx.file.pkgconfig_template.read()
    
    # Generate PKG-CONFIG files for different configurations
    configs = {
        "dal-static-threading-host": {
            "libdir": "lib/intel64",
            "libs": "-L${libdir} -lonedal -lonedal_core -lonedal_thread -lonedal_parameters -ltbb -ltbbmalloc -lpthread -ldl",
            "opts": "-std=c++17 -Wno-deprecated-declarations -I${includedir}"
        },
        "dal-dynamic-threading-host": {
            "libdir": "lib/intel64",
            "libs": "-L${libdir} -lonedal -lonedal_core -lonedal_thread -lonedal_parameters -ltbb -ltbbmalloc -lpthread -ldl",
            "opts": "-std=c++17 -Wno-deprecated-declarations -I${includedir}"
        }
    }
    
    dst_files = []
    for config_name, config_data in configs.items():
        content = template_content.format(**config_data)
        pc_path = paths.join(prefix, "lib", "pkgconfig", config_name + ".pc")
        pc_file = ctx.actions.declare_file(pc_path)
        ctx.actions.write(
            output = pc_file,
            content = content,
        )
        dst_files.append(pc_file)
    
    return dst_files

def _generate_cmake_files(ctx, prefix):
    """Generate CMake files using templates with variable substitution"""
    # Read template file
    template_content = ctx.file.cmake_template.read()
    
    # Variable substitutions similar to make system
    substitutions = {
        "@DAL_ROOT_REL_PATH@": "../..",
        "@VERSIONS_SET@": "TRUE",
        "@DAL_VER_MAJOR_BIN@": "2025",
        "@DAL_VER_MINOR_BIN@": "8",
        "@ARCH_DIR_ONEDAL@": "intel64",
        "@INC_REL_PATH@": "include",
        "@DLL_REL_PATH@": "lib/intel64"
    }
    
    # Apply substitutions
    content = template_content
    for key, value in substitutions.items():
        content = content.replace(key, value)
    
    cmake_path = paths.join(prefix, "lib", "cmake", "oneDAL", "oneDALConfig.cmake")
    cmake_file = ctx.actions.declare_file(cmake_path)
    ctx.actions.write(
        output = cmake_file,
        content = content,
    )
    
    return cmake_file

def _copy_to_release_impl(ctx):
    extra_toolchain = ctx.toolchains["@onedal//dev/bazel/toolchains:extra"]
    prefix = ctx.attr.name + "/daal/latest"
    files = []
    files += _copy_include(ctx, prefix)
    files += _copy_lib(ctx, prefix)
    
    # Copy examples if provided
    if ctx.attr.examples:
        files += _copy_examples(ctx, prefix)
    
    # Copy data files if provided
    if ctx.attr.data_files:
        files += _copy_data_files(ctx, prefix)
    
    # Copy environment scripts from deploy/local
    if ctx.attr.env_scripts:
        files += _copy_env_scripts(ctx, prefix)
    
    # Generate PKG-CONFIG files using template
    if ctx.file.pkgconfig_template:
        files += _generate_pkgconfig_files(ctx, prefix)
    
    # Generate CMake files using template
    if ctx.file.cmake_template:
        cmake_file = _generate_cmake_files(ctx, prefix)
        files.append(cmake_file)
    
    return [DefaultInfo(files=depset(files))]

_release = rule(
    implementation = _copy_to_release_impl,
    attrs = {
        "include": attr.label_list(allow_files=True),
        "include_prefix": attr.string_list(),
        "include_skip_prefix": attr.string_list(),
        "lib": attr.label_list(allow_files=True),
        "examples": attr.label_list(allow_files=True, default=[]),
        "data_files": attr.label_list(allow_files=True, default=[]),
        "env_scripts": attr.label_list(allow_files=True, default=[]),
        "pkgconfig_template": attr.label(allow_single_file=True, default=None),
        "cmake_template": attr.label(allow_single_file=True, default=None),
    },
    toolchains = [
        "@onedal//dev/bazel/toolchains:extra"
    ],
)

def _headers_filter_impl(ctx):
    all_headers = []
    for dep in ctx.attr.deps:
        all_headers += _collect_headers(dep)
    all_headers = utils.unique_files(all_headers)
    filtered_headers = []
    for header in all_headers:
        if (_match_file_name(header, ctx.attr.include) and
            not _match_file_name(header, ctx.attr.exclude)):
            filtered_headers.append(header)
    return [
        DefaultInfo(files = depset(filtered_headers))
    ]


headers_filter = rule(
    implementation = _headers_filter_impl,
    attrs = {
        "deps": attr.label_list(allow_files=True),
        "include": attr.string_list(),
        "exclude": attr.string_list(),
    },
)

def release_include(hdrs, skip_prefix="", add_prefix=""):
    return (hdrs, add_prefix, skip_prefix)

def release(name, include, lib, examples=[], data_files=[], env_scripts=[], pkgconfig_template=None, cmake_template=None):
    rule_include = []
    rule_include_prefix = []
    rule_include_skip_prefix = []
    for hdrs, prefix, skip_prefix in include:
        for dep in hdrs:
            rule_include.append(dep)
            rule_include_prefix.append(prefix)
            rule_include_skip_prefix.append(skip_prefix)
    _release(
        name = name,
        include = rule_include,
        include_prefix = rule_include_prefix,
        include_skip_prefix = rule_include_skip_prefix,
        lib = lib,
        examples = examples,
        data_files = data_files,
        env_scripts = env_scripts,
        pkgconfig_template = pkgconfig_template,
        cmake_template = cmake_template,
    )
