package(default_visibility = ["//visibility:public"])
load("@onedal//dev/bazel:dal.bzl",
    "dal_module",
    "dal_test_suite",
)

dal_module(
    name = "micromkl",
    auto = True,
    dal_deps = [
        "@onedal//cpp/oneapi/dal:common",
    ],
)

dal_test_suite(
    name = "tests",
    framework = "catch2",
    private = True,
    dal_deps = [],
)
