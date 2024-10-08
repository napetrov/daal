/*******************************************************************************
* Copyright 2022 Intel Corporation
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

#include <algorithm>
#include <cmath>
#include <limits>
#include <numeric>
#include <random>
#include <vector>

#include "oneapi/dal/algo/linear_regression/common.hpp"
#include "oneapi/dal/algo/linear_regression/train.hpp"
#include "oneapi/dal/algo/linear_regression/infer.hpp"

#include "oneapi/dal/table/homogen.hpp"
#include "oneapi/dal/table/row_accessor.hpp"
#include "oneapi/dal/table/detail/table_builder.hpp"

#include "oneapi/dal/test/engine/fixtures.hpp"
#include "oneapi/dal/test/engine/math.hpp"

#include "oneapi/dal/test/engine/metrics/regression.hpp"

namespace oneapi::dal::linear_regression::test {

namespace te = dal::test::engine;
namespace de = dal::detail;
namespace la = te::linalg;

template <typename TestType, typename Derived>
class lr_test : public te::crtp_algo_fixture<TestType, Derived> {
public:
    using float_t = std::tuple_element_t<0, TestType>;
    using method_t = std::tuple_element_t<1, TestType>;
    using task_t = std::tuple_element_t<2, TestType>;

    using train_input_t = train_input<task_t>;
    using train_result_t = train_result<task_t>;
    using test_input_t = infer_input<task_t>;
    using test_result_t = infer_result<task_t>;

    te::table_id get_homogen_table_id() const {
        return te::table_id::homogen<float_t>();
    }

    Derived* get_impl() {
        return static_cast<Derived*>(this);
    }

    table compute_responses(const table& beta, const table& bias, const table& data) const {
        const auto s_count = data.get_row_count();

        REQUIRE(beta.get_row_count() == this->r_count_);
        REQUIRE(beta.get_column_count() == this->f_count_);

        REQUIRE(bias.get_row_count() == std::int64_t(1));
        REQUIRE(bias.get_column_count() == this->r_count_);

        auto res_arr = array<float_t>::zeros(s_count * this->r_count_);

        const auto beta_arr = row_accessor<const float_t>(beta).pull({ 0, -1 });
        const auto bias_arr = row_accessor<const float_t>(bias).pull({ 0, -1 });
        const auto data_arr = row_accessor<const float_t>(data).pull({ 0, -1 });

        for (std::int64_t s = 0; s < s_count; ++s) {
            for (std::int64_t r = 0; r < this->r_count_; ++r) {
                for (std::int64_t f = 0; f < this->f_count_; ++f) {
                    const auto& v = data_arr[s * this->f_count_ + f];
                    const auto& b = beta_arr[r * this->f_count_ + f];
                    *(res_arr.get_mutable_data() + s * this->r_count_ + r) += v * b;
                }
            }
        }

        for (std::int64_t s = 0; s < s_count; ++s) {
            for (std::int64_t r = 0; r < this->r_count_; ++r) {
                *(res_arr.get_mutable_data() + s * this->r_count_ + r) += bias_arr[r];
            }
        }

        return homogen_table::wrap(res_arr, s_count, this->r_count_);
    }

    std::tuple<table, table> generate_betas(std::int64_t seed) const {
        std::mt19937 meta_gen(seed);
        std::tuple<table, table> result{ {}, {} };

        const std::int64_t betas_seed = meta_gen();
        const auto betas_dataframe = GENERATE_DATAFRAME(
            te::dataframe_builder{ this->r_count_, this->f_count_ }.fill_uniform(-10.1,
                                                                                 10.1,
                                                                                 betas_seed));
        std::get<0>(result) = betas_dataframe.get_table(this->get_homogen_table_id());

        if (this->intercept_) {
            const std::int64_t bias_seed = meta_gen();
            const auto bias_dataframe = GENERATE_DATAFRAME(
                te::dataframe_builder{ std::int64_t(1), this->r_count_ }.fill_uniform(-15.5,
                                                                                      15.5,
                                                                                      bias_seed));
            std::get<1>(result) = bias_dataframe.get_table(this->get_homogen_table_id());
        }
        else {
            auto bias_arr = array<float_t>::zeros(this->r_count_);
            std::get<1>(result) = homogen_table::wrap(bias_arr, std::int64_t(1), this->r_count_);
        }

        return result;
    }

    void check_table_dimensions(const table& x_train,
                                const table& y_train,
                                const table& x_test,
                                const table& y_test) {
        REQUIRE(x_train.get_column_count() == this->f_count_);
        REQUIRE(x_train.get_row_count() == this->s_count_);
        REQUIRE(x_test.get_column_count() == this->f_count_);
        REQUIRE(x_test.get_row_count() == this->t_count_);
        REQUIRE(y_train.get_column_count() == this->r_count_);
        REQUIRE(y_train.get_row_count() == this->s_count_);
        REQUIRE(y_test.get_column_count() == this->r_count_);
        REQUIRE(y_test.get_row_count() == this->t_count_);
    }

    void generate(std::int64_t seed = 777) {
        this->get_impl()->generate_dimensions();

        auto [beta, bias] = generate_betas(seed);

        this->bias_ = std::move(bias);
        this->beta_ = std::move(beta);
    }

    auto get_descriptor() const {
        result_option_id resopts = result_options::coefficients;
        if (this->intercept_)
            resopts = resopts | result_options::intercept;
        return linear_regression::descriptor<float_t, method_t, task_t>(intercept_)
            .set_result_options(resopts);
    }

    void check_if_close(const table& left, const table& right, double tol = 1e-3) {
        constexpr auto eps = std::numeric_limits<float_t>::epsilon();

        const auto c_count = left.get_column_count();
        const auto r_count = left.get_row_count();

        REQUIRE(right.get_column_count() == c_count);
        REQUIRE(right.get_row_count() == r_count);

        row_accessor<const float_t> lacc(left);
        row_accessor<const float_t> racc(right);

        const auto larr = lacc.pull({ 0, -1 });
        const auto rarr = racc.pull({ 0, -1 });

        for (std::int64_t r = 0; r < r_count; ++r) {
            for (std::int64_t c = 0; c < c_count; ++c) {
                const auto lval = larr[r * c_count + c];
                const auto rval = rarr[r * c_count + c];

                CAPTURE(r_count, c_count, r, c, lval, rval);

                const auto aerr = std::abs(lval - rval);
                if (aerr < tol)
                    continue;

                const auto den = std::max({ eps, //
                                            std::abs(lval),
                                            std::abs(rval) });

                const auto rerr = aerr / den;
                CAPTURE(aerr, rerr, den, r, c, lval, rval);
                REQUIRE(rerr < tol);
            }
        }
    }

    void run_and_check(std::int64_t seed = 888, double tol = 1e-2) {
        using namespace ::oneapi::dal::detail;

        std::mt19937 meta_gen(seed);

        const std::int64_t train_seed = meta_gen();
        const auto train_dataframe = GENERATE_DATAFRAME(
            te::dataframe_builder{ this->s_count_, this->f_count_ }.fill_uniform(-5.5,
                                                                                 3.5,
                                                                                 train_seed));
        auto x_train = train_dataframe.get_table(this->get_homogen_table_id());

        const std::int64_t test_seed = meta_gen();
        const auto test_dataframe = GENERATE_DATAFRAME(
            te::dataframe_builder{ this->t_count_, this->f_count_ }.fill_uniform(-3.5,
                                                                                 5.5,
                                                                                 test_seed));
        auto x_test = test_dataframe.get_table(this->get_homogen_table_id());

        auto y_train = compute_responses(this->beta_, this->bias_, x_train);
        auto y_test = compute_responses(this->beta_, this->bias_, x_test);

        check_table_dimensions(x_train, y_train, x_test, y_test);

        const auto desc = this->get_descriptor();
        const auto train_res = this->train(desc, x_train, y_train);

        SECTION("Checking intercept values") {
            if (desc.get_result_options().test(result_options::intercept))
                check_if_close(train_res.get_intercept(), this->bias_, tol);
        }

        SECTION("Checking coefficient values") {
            if (desc.get_result_options().test(result_options::coefficients))
                check_if_close(train_res.get_coefficients(), this->beta_, tol);
        }

        const auto infer_res = this->infer(desc, x_test, train_res.get_model());

        SECTION("Checking infer results") {
            check_if_close(infer_res.get_responses(), y_test, tol);
        }
    }

protected:
    bool intercept_ = true;
    std::int64_t t_count_;
    std::int64_t s_count_;
    std::int64_t f_count_;
    std::int64_t r_count_;

    table bias_;
    table beta_;
};

using lr_types = COMBINE_TYPES((float, double),
                               (linear_regression::method::norm_eq),
                               (linear_regression::task::regression));

} // namespace oneapi::dal::linear_regression::test
