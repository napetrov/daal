/*******************************************************************************
* Copyright contributors to the oneDAL project
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

#include "oneapi/dal/algo/correlation_distance.hpp"
#include "oneapi/dal/io/csv.hpp"

#include "example_util/utils.hpp"

namespace dal = oneapi::dal;

int main(int argc, char const *argv[]) {
    const auto x_data_file_name = get_data_path("x_distance.csv");
    const auto y_data_file_name = get_data_path("y_distance.csv");

    const auto x = dal::read<dal::table>(dal::csv::data_source{ x_data_file_name });
    const auto y = dal::read<dal::table>(dal::csv ::data_source{ y_data_file_name });
    const auto distance_desc = dal::correlation_distance::descriptor{};

    const auto result = dal::compute(distance_desc, x, y);

    std::cout << "Values:\n" << result.get_values() << std::endl;

    return 0;
}
