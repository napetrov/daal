/*******************************************************************************
* Copyright 2020 Intel Corporation
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*     http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*******************************************************************************/

#include "oneapi/dal/io/csv/detail/read_ops.hpp"
#include "oneapi/dal/backend/dispatcher.hpp"
#include "oneapi/dal/io/csv/backend/cpu/read_kernel.hpp"
#include "oneapi/dal/table/csr.hpp"

namespace oneapi::dal::csv::detail {
namespace v1 {

using dal::detail::host_policy;

template <typename Float>
table read_ops_dispatcher<table, Float, host_policy>::operator()(
    const host_policy& policy,
    const data_source_base& ds,
    const read_args<table>& args) const {
    using kernel_dispatcher_t = dal::backend::kernel_dispatcher< //
        KERNEL_SINGLE_NODE_CPU(backend::read_kernel_cpu<table, Float>)>;
    return kernel_dispatcher_t()(policy, ds, args);
}

template <typename Float>
csr_table read_ops_dispatcher<csr_table, Float, host_policy>::operator()(
    const host_policy& policy,
    const data_source_base& ds,
    const read_args<csr_table>& args) const {
    using kernel_dispatcher_t = dal::backend::kernel_dispatcher< //
        KERNEL_SINGLE_NODE_CPU(backend::read_kernel_cpu<csr_table, Float>)>;
    return kernel_dispatcher_t()(policy, ds, args);
}

#define INSTANTIATE(F) template struct ONEDAL_EXPORT read_ops_dispatcher<table, F, host_policy>;
INSTANTIATE(float)
INSTANTIATE(double)

#define INSTANTIATE_CSR(F) \
    template struct ONEDAL_EXPORT read_ops_dispatcher<csr_table, F, host_policy>;
INSTANTIATE_CSR(float)
INSTANTIATE_CSR(double)

} // namespace v1
} // namespace oneapi::dal::csv::detail
