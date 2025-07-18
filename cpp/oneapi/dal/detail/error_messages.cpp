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

#include "oneapi/dal/detail/error_messages.hpp"

#define MSG(id, text)                           \
    const char* error_messages::id() noexcept { \
        return text;                            \
    }

namespace oneapi::dal::detail {
namespace v1 {

/* Common */
MSG(array_does_not_contain_mutable_data, "Array does not contain mutable data")
MSG(algorithm_is_not_implemented_for_this_device,
    "Algorithm is not implemented for this device. "
    "Consider running on it on the other device.")
MSG(feature_index_is_out_of_range, "Feature index is out of range")
MSG(incompatible_array_reinterpret_cast_types,
    "Cannot reinterpret array to provided type, "
    "because resulting array size would not match source array size")
MSG(only_homogen_table_is_supported, "Only homogen table is supported")
MSG(overflow_found_in_multiplication_of_two_values,
    "Overflow found in multiplication of two values")
MSG(overflow_found_in_sum_of_two_values, "Overflow found in sum of two values")
MSG(unknown_status_code, "Unknown status code")
MSG(unsupported_data_layout, "Unsupported data layout")
MSG(unsupported_data_type, "Requested data type is not supported")
MSG(unsupported_device_type, "Requested device type is not supported")
MSG(small_data_block, "Data block size is smaller than expected")
MSG(spmd_version_of_algorithm_is_not_implemented,
    "SPMD version of the algorithm is not implemented")
MSG(spmd_version_of_algorithm_is_not_implemented_for_this_device,
    "SPMD version of the algorithm is not implemented for this device. "
    "Consider running on it on the other device.")
MSG(integral_type_conversion_overflow, "Integral type conversion overflow")
MSG(integral_type_conversion_underflow, "Integral type conversion underflow")
MSG(invalid_data_block_size, "Invalid data block size")
MSG(invalid_column_indices_block_size, "Invalid column indices block size")
MSG(method_not_implemented, "Method is not implemented")
MSG(negative_integral_value_conversion_to_unsigned,
    "Negative integral value conversion to unsigned")
MSG(unsupported_feature_type, "Feature type is not supported")
MSG(unknown_memcpy_error, "Unknown error during memory copying")
MSG(unknown_usm_pointer_type, "USM pointer type is unknown in the current context")
MSG(queues_in_different_contexts, "Provided queues are in different contexts")
MSG(unsupported_usm_alloc, "Requested USM alloc type is not supported")
MSG(page_size_leq_zero, "Page size is lower than or equal to zero")
MSG(invalid_key, "Cannot find the given key")
MSG(capacity_leq_zero, "Capacity is lower than or equal to zero")
MSG(empty_set_of_result_options, "Empty set of result options")
MSG(this_result_is_not_enabled_via_result_options, "This result is not enabled via result options")
MSG(spmd_error_holder_message, "SPMD failure occurred, use e.rethrow_actual() to get actual error")
MSG(spmd_coworker_failure, "SPMD execution was interrupted because of coworker's failure")
MSG(unexpected_dataset_type, "Unexpected dataset type")

/* Primitives */
MSG(invalid_number_of_elements_to_process, "Invalid number of elements to process")
MSG(invalid_number_of_elements_to_sort, "Invalid number of elements to sort")
MSG(failed_to_compute_eigenvectors, "Failed to compute eigenvectors")
MSG(failed_to_generate_random_numbers, "Failed to generate random numbers")

/* Tables */
MSG(allocated_memory_size_is_not_enough_to_copy_data,
    "Allocated memory size is not enough to copy the data")
MSG(cannot_get_data_type_from_empty_metadata, "Cannot get data type from empty metadata")
MSG(cannot_get_feature_type_from_empty_metadata, "Cannot get feature type from empty metadata")
MSG(element_count_in_data_type_and_feature_type_arrays_does_not_match,
    "Element count in data type and feature type array does not match")
MSG(pulling_column_is_not_supported_for_dpc, "Pulling column is not supported for DPC++")
MSG(pulling_column_is_not_supported, "Pulling column is not supported")
MSG(pulling_rows_is_not_supported_for_dpc, "Pulling rows is not supported for DPC++")
MSG(pulling_rows_is_not_supported, "Pulling rows is not supported")
MSG(pushing_column_is_not_supported_for_dpc, "Pushing column is not supported for DPC++")
MSG(pushing_column_is_not_supported, "Pushing column is not supported")
MSG(pushing_rows_is_not_supported_for_dpc, "Pushing rows is not supported for DPC++")
MSG(pushing_rows_is_not_supported, "Pushing rows is not supported")
MSG(rc_and_cc_do_not_match_element_count_in_array,
    "Row count and column count do not match element count in array")
MSG(rc_leq_zero, "Row count is lower than or equal to zero")
MSG(cc_leq_zero, "Column count is lower than or equal to zero")
MSG(object_does_not_provide_read_access_to_rows,
    "Given object does not provide read access to rows")
MSG(object_does_not_provide_write_access_to_rows,
    "Given object does not provide write access to rows")
MSG(object_does_not_provide_read_access_to_columns,
    "Given object does not provide read access to columns")
MSG(object_does_not_provide_write_access_to_columns,
    "Given object does not provide write access to columns")
MSG(object_does_not_provide_access_to_rows_or_columns,
    "Given object does not provide access to rows or columns")
MSG(unsupported_conversion_types, "Unsupported conversion types")
MSG(invalid_first_row_offset, "Invalid row offset for the first row is provided")
MSG(row_offsets_lt_min_value, "Row offsets are less than the minimum acceptable value")
MSG(row_offsets_gt_max_value, "Row offsets are larger than the maximum acceptable value")
MSG(row_offsets_not_ascending, "Row offsets are are not stored in the ascending order")
MSG(row_offsets_pointer_is_null, "Null input row offsets pointer is not supported")
MSG(column_indices_lt_min_value, "Column indices are less than the minimum acceptable value")
MSG(column_indices_gt_max_value, "Column indices are larger than the maximum acceptable value")
MSG(zero_based_indexing_is_not_supported, "Zero-based indexing is not supported for CSR table")
MSG(object_does_not_provide_read_access_to_csr,
    "Given object does not provide read access to the block of CSR format")
MSG(pull_column_interface_is_not_implemented,
    "Pull column interface is planned but not implemented yet")

/* Ranges */
MSG(invalid_range_of_rows, "Invalid range of rows")
MSG(invalid_range_of_columns, "Invalid range of columns")
MSG(column_index_out_of_range, "Column index out of range")

/* RNG */
MSG(rng_engine_does_not_support_parallelization_techniques,
    "Random number generation engine doesn't support parallelization techniques")
MSG(rng_engine_is_not_supported, "Random number generation engine isn't supported")

/* Graphs */
MSG(vertex_index_out_of_range_expect_from_zero_to_vertex_count,
    "Vertex index is out of range, expect index in [0, vertex_count)")
MSG(negative_vertex_id, "Negative vertex ID")
MSG(unimplemented_sorting_procedure, "Unimplemented sorting procedure")
MSG(edge_values_are_empty, "Edge values are empty")

/* IO */
MSG(file_not_found, "File not found")
MSG(unsupported_read_mode, "Unsupported read mode")
MSG(invalid_sparse_indexing,
    "Invalid sparse indexing type. "
    "Supported values are zero_based and one_based")
MSG(invalid_csr_format,
    "Invalid CSR format. "
    "Expected three lines: row offsets, column indices, and non-zero elements")
MSG(invalid_feature_count, "Invalid feature count")

/* Serialization */
MSG(object_is_not_serializable, "Object is not serializable")
MSG(archive_content_does_not_match_type, "Archive content does not match requested type")
MSG(archive_is_in_invalid_state,
    "Archive state is invalid. It may indicate that "
    "serialization or deserialization was interupted by an exception")

/* General algorithms */
MSG(accuracy_threshold_lt_zero, "Accuracy_threshold is lower than zero")
MSG(class_count_leq_one, "Class count is lower than or equal to one")
MSG(conv_tol_lt_zero, "Convergence tolerance is less than zero")
MSG(input_data_is_empty, "Input data is empty")
MSG(input_data_rc_neq_input_responses_rc,
    "Input data row count is not equal to input responses row count")
MSG(input_data_rc_neq_input_weights_rc,
    "Input data row count is not equal to input weights row count")
MSG(input_responses_are_empty, "Responses are empty")
MSG(input_responses_contain_only_one_unique_value_expect_two,
    "Input responses contain only one unique value, two unique values are expected")
MSG(input_responses_contain_wrong_unique_values_count_expect_two,
    "Input labels contain wrong number of unique values, two unique values are expected")
MSG(input_responses_table_has_wrong_cc_expect_one,
    "Input responses table has wrong column count, one column is expected")
MSG(iteration_count_lt_zero, "Iteration count is lower than zero")
MSG(max_iteration_count_leq_zero, "Max iteration count lower than or equal to zero")
MSG(max_iteration_count_lt_zero, "Max iteration count lower than zero")

/* K-Means */
MSG(cluster_count_leq_zero, "Cluster count is lower than or equal to zero")
MSG(cluster_count_exceeds_data_row_count, "Cluster count exceeds data row count")
MSG(cluster_count_gt_max_int32, "Cluster count is greater than max int32 value")
MSG(row_count_gt_max_int32, "Row count is greater than max int32 value")
MSG(input_initial_centroids_are_empty, "Input initial centroids are empty")
MSG(input_initial_centroids_cc_neq_input_data_cc,
    "Input initial centroids column count is not equal to input data column count")
MSG(input_initial_centroids_rc_neq_desc_cluster_count,
    "Input initial centroids row count is not equal to descriptor cluster count")
MSG(input_model_centroids_are_empty, "Input model centroids are empty")
MSG(input_model_centroids_cc_neq_input_data_cc,
    "Input model centroids column count is not equal to input data column count")
MSG(input_model_centroids_rc_neq_desc_cluster_count,
    "Input model centroids row count is not equal to descriptor cluster count")
MSG(kmeans_init_csr_methods_are_not_implemented_for_gpu,
    "K-Means init methods for CSR data are not implemented for GPU")
MSG(kmeans_init_parallel_plus_dense_method_is_not_implemented_for_gpu,
    "K-Means init++ parallel dense method is not implemented for GPU")
MSG(kmeans_init_plus_plus_dense_method_is_not_implemented_for_gpu,
    "K-Means init++ dense method is not implemented for GPU")
MSG(objective_function_value_lt_zero, "Objective function value is lower than zero")

/* k-NN */
MSG(knn_kd_tree_method_is_not_implemented_for_gpu,
    "k-NN k-d tree method is not implemented for GPU")
MSG(knn_regression_task_is_not_implemented_for_cpu,
    "k-NN regression task is not implemented for CPU")
MSG(knn_search_task_is_not_implemented_for_gpu, "k-NN search task is not implemented for GPU")
MSG(neighbor_count_lt_one, "Neighbor count lower than one")
MSG(unknown_distance_type,
    "Custom distances for k-NN is not supported, use one of the predefined distances instead.")
MSG(distance_is_not_supported_for_gpu,
    "Only Minkowski, Cosine, Chebyshev and Euclidean distances are supported for GPU")
MSG(incompatible_knn_model,
    "The provided model is incompatible with the selected k-NN task or method")
MSG(invalid_set_of_result_options_to_search,
    "Provided results options are incompatible with the search task. Search task cannot compute responses.")

/* Minkowski distance */
MSG(invalid_minkowski_degree, "Minkowski degree should be greater than zero")

/* Objective function */
MSG(resp_column_count_is_not_eq_to_one, "Responses should be a table of size n*1")
MSG(params_column_count_is_not_eq_to_one, "Parameters should be a table of size (p + 1) * 1")
MSG(value_is_not_provided, "Table with value is missing")
MSG(gradient_is_not_provided, "Table with gradient is missing")
MSG(hessian_is_not_provided, "Table with hessian is missing")
MSG(incorrect_output_table_size, "On of the tables sizes in result is not correct")
MSG(regularization_coef_is_less_than_zero,
    "L1 and L2 regularization coefs should not be less than zero")
MSG(regularization_coef_is_nan_or_inf,
    "L1 and L2 regularization coefs should be real decimal numbers")

/* Optimizers */
MSG(matrix_is_not_positively_definite,
    "Matrix passed to conjugate gradients solver should be positively defined")

/* Jaccard */
MSG(column_begin_gt_column_end, "Column begin is greater than column end")
MSG(empty_edge_list, "Empty edge list")
MSG(interval_gt_vertex_count, "Interval is greater than vertex count")
MSG(negative_interval, "Negative interval")
MSG(row_begin_gt_row_end, "Row begin is greater than row end")
MSG(range_idx_gt_max_int32, "Range indexes are greater than max of int32")

/* Subgraph Isomorphism */
MSG(max_match_count_lt_zero, "Maximum number of match count less that zero")
MSG(empty_target_graph, "Empty target graph")
MSG(empty_pattern_graph, "Empty pattern graph")
MSG(subgraph_isomorphism_is_not_implemented_for_labeled_edges,
    "Subgraph isomorphism is not implemented for labeled edges")
MSG(incorrect_index_is_returned, "Internal error: incorrect index is returned")
MSG(invalid_vertex_edge_attributes, "Internal error: invalid vertex/edge attributes")
MSG(target_graph_is_smaller_than_pattern_graph, "Target graph is smaller than pattern graph")

/* PCA */
MSG(component_count_lt_zero, "Component count is lower than zero")
MSG(input_data_cc_lt_desc_component_count,
    "Input data column count is lower than component count provided in descriptor")
MSG(input_model_eigenvectors_cc_neq_input_data_cc,
    "Input model eigenvectors column count is not equal to input data column count")
MSG(input_model_eigenvectors_rc_neq_desc_component_count,
    "Eigenvectors' row count in input model is not equal to component count provided in descriptor")
MSG(input_model_eigenvectors_rc_neq_input_data_cc,
    "Eigenvectors' row count in input model is not equal to input data column count")
MSG(pca_svd_based_method_is_not_implemented_for_gpu,
    "PCA SVD-based method is not implemented for GPU")

/* Shortest Paths */
MSG(negative_source, "Source vertex is lower than zero")
MSG(source_gte_vertex_count, "Source vertex is out of range")
MSG(negative_delta, "Delta parameter is lower than zero")
MSG(nothing_to_compute, "Invalid combination of optional results: nothing to compute")
MSG(distances_are_uninitialized, "Distances are not set as an optional result")
MSG(predecessors_are_uninitialized, "Predecessors are not set as an optional result")

/* SVM */
MSG(c_leq_zero, "C is lower than or equal to zero")
MSG(cache_size_lt_zero, "Cache size is lower than zero")
MSG(degree_lt_zero, "Degree lower than zero")
MSG(input_model_coeffs_are_empty, "Input model coeffs are empty")
MSG(input_model_coeffs_rc_neq_input_model_support_vector_count,
    "Input model coeffs row count is not equal to support vector count provided in input model")
MSG(input_model_does_not_match_kernel_function, "Input model does not match kernel function type")
MSG(input_model_support_vectors_are_empty, "Input model support vectors are empty")
MSG(input_model_support_vectors_cc_neq_input_data_cc,
    "Input model support vectors column count is not equal to input data column count")
MSG(input_model_support_vectors_rc_neq_input_model_support_vector_count,
    "Support vectors row count is not equal to support vector count in input model")
MSG(nu_gt_one, "Nu is greater than one")
MSG(nu_leq_zero, "Nu is lower than or equal to zero")
MSG(nu_svm_smo_method_is_not_implemented_for_gpu, "nuSVM SMO method is not implemented for GPU")
MSG(nu_svm_thunder_method_is_not_implemented_for_gpu,
    "nuSVM Thunder method is not implemented for GPU")
MSG(polynomial_kernel_is_not_implemented_for_gpu, "Polynomial kernel is not implemented for GPU")
MSG(sigmoid_kernel_is_not_implemented_for_gpu, "Sigmoid kernel is not implemented for GPU")
MSG(sigma_leq_zero, "Sigma lower than or equal to zero")
MSG(svm_multiclass_not_implemented_for_gpu,
    "SVM with multiclass support is not implemented for GPU")
MSG(svm_nu_classification_task_is_not_implemented_for_gpu,
    "Classification nuSVM is not implemented for GPU")
MSG(svm_nu_regression_task_is_not_implemented_for_gpu,
    "Regression nuSVM is not implemented for GPU")
MSG(svm_regression_task_is_not_implemented_for_gpu, "Regression SVM is not implemented for GPU")
MSG(svm_smo_method_is_not_implemented_for_gpu, "SVM SMO method is not implemented for GPU")
MSG(tau_leq_zero, "Tau is lower than or equal to zero")
MSG(epsilon_lt_zero, "Epsilon is lower than zero")
MSG(unknown_kernel_function_type, "Unknown kernel function type")

/* Kernel Functions */
MSG(input_x_cc_neq_y_cc, "Input x column count is not qual to y column count")
MSG(input_x_is_empty, "Input x is empty")
MSG(input_y_is_empty, "Input y is empty")

/* Linear Regression */
MSG(intercept_result_option_requires_intercept_flag,
    "Intercept result option requires intercept flag")
MSG(too_small_singular_values,
    "Linear system has too small singular values, cannot calculate a solution")

/* Logistic Regression */
MSG(class_count_neq_two,
    "Only binary classification is supported so class count should be equal to 2")
MSG(inverse_regularization_leq_zero, "Inverse regularization factor should be a positive number")
MSG(l1_coef_neq_zero,
    "Currently L1 regularization is not supported, so l1_coef should be equal to zero")
MSG(log_reg_dense_batch_method_is_not_implemented_for_cpu,
    "LogisticRegression is not implemented for CPU")
MSG(log_reg_sparse_method_is_not_implemented_for_cpu,
    "LogisticRegression does not have sparsity support for CPU")
MSG(unknown_optimizer, "Custom optimizers are not supported, use on of provided by the library")

/* Decision Forest */
MSG(bootstrap_is_incompatible_with_error_metric,
    "Values of bootstrap and error metric parameters provided "
    "in descriptor are incompatible to each other")
MSG(bootstrap_is_incompatible_with_variable_importance_mode,
    "Values of bootstrap and variable importance mode parameters provided "
    "in descriptor are incompatible to each other")
MSG(decision_forest_train_dense_method_is_not_implemented_for_gpu,
    "Decision forest train dense method is not implemented for GPU")
MSG(decision_forest_train_hist_method_is_not_implemented_for_cpu,
    "Decision forest train hist method is not implemented for CPU")
MSG(input_model_is_not_initialized, "Input model is not initialized")
MSG(not_enough_memory_to_build_one_tree, "There isn't enough memory to build one tree")
MSG(not_enough_local_memory_for_hist, "There is not enough local memory to build one histogram")
MSG(invalid_number_of_trees, "Invalid number of trees")
MSG(invalid_number_of_min_observations_in_leaf_node,
    "Invalid number of min observations in leaf node")
MSG(invalid_number_of_feature_per_node, "Invalid number of features per node")
MSG(invalid_number_of_max_bins, "Invalid max number of bins")
MSG(invalid_value_for_min_bin_size, "Invalid value for min bin size")
MSG(invalid_number_of_classes, "Invalid number of classes")
MSG(invalid_value_for_observations_per_tree_fraction,
    "Invalid value for observations per tree fraction")
MSG(input_model_tree_has_invalid_size, "Input model tree size is invalid")

/* DBSCAN */
MSG(weight_dimension_doesnt_match_data_dimension,
    "Weights dimensions doesn't match data dimensions")
MSG(weights_column_count_ne_1, "Weights is not a single-column table")

/* Louvain */
MSG(negative_resolution, "Resolution parameter is lower than zero")
MSG(input_initial_partition_table_rc_neq_vertex_count,
    "Input initial partition table row count is not equal to vertex count")
MSG(input_initial_partition_table_has_wrong_cc_expect_one,
    "Input initial partition table has wrong column count, one column is expected")
MSG(negative_initial_partition_label, "Input initial partition label is negative")
MSG(initial_partition_label_gte_vertex_count,
    "Input initial partition label is greater than or equal to vertex count")

/* SPMD */
MSG(unsupported_communicator_backend, "SPMD: unsupported communicator backend")
MSG(invalid_data_type, "SPMD: invalid data type")
MSG(invalid_op,
    "SPMD: invalid operation. Only predefined reduction and other operations can be used")
MSG(invalid_buffer, "SPMD: invalid buffer pointer")
MSG(invalid_count, "SPMD: invalid data count")
MSG(invalid_mpi_comm, "SPMD: invalid mpi communicator")
MSG(invalid_root, "SPMD: invalid root")
MSG(unknown_mpi_error, "SPMD: unknown MPI error")
MSG(sendrecv_replace_is_not_implemented_for_threaded_communicator,
    "SPMD: sendrecv_replace communicator method is implemented only for MPI and CCL backend")

} // namespace v1
} // namespace oneapi::dal::detail
