/* file: kdtree_knn_dense_batch.cpp */
/*******************************************************************************
* Copyright 2014 Intel Corporation
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

/*
!  Content:
!    C++ example of k-Nearest Neighbor in the batch processing mode.
!******************************************************************************/

/**
 * <a name="DAAL-EXAMPLE-CPP-KDTREE_KNN_DENSE_BATCH"></a>
 * \example kdtree_knn_dense_batch.cpp
 */

#include "daal.h"
#include "service.h"
#include <cstdio>

using namespace daal;
using namespace daal::algorithms;
using namespace daal::data_management;

/* Input data set parameters */
const std::string trainDatasetFileName = "../data/batch/k_nearest_neighbors_train.csv";
const std::string testDatasetFileName = "../data/batch/k_nearest_neighbors_test.csv";

size_t nFeatures = 5;
size_t nClasses = 5;

kdtree_knn_classification::training::ResultPtr trainingResult;
kdtree_knn_classification::prediction::ResultPtr predictionResult;
NumericTablePtr testGroundTruth;

void trainModel();
void testModel();
void printResults();

int main(int argc, char* argv[]) {
    checkArguments(argc, argv, 2, &trainDatasetFileName, &testDatasetFileName);

    trainModel();
    testModel();
    printResults();

    return 0;
}

void trainModel() {
    /* Initialize FileDataSource<CSVFeatureManager> to retrieve the input data from a .csv file */
    FileDataSource<CSVFeatureManager> trainDataSource(trainDatasetFileName,
                                                      DataSource::notAllocateNumericTable,
                                                      DataSource::doDictionaryFromContext);

    /* Create Numeric Tables for training data and labels */
    NumericTablePtr trainData(new HomogenNumericTable<>(nFeatures, 0, NumericTable::doNotAllocate));
    NumericTablePtr trainGroundTruth(new HomogenNumericTable<>(1, 0, NumericTable::doNotAllocate));
    NumericTablePtr mergedData(new MergedNumericTable(trainData, trainGroundTruth));

    /* Retrieve the data from the input file */
    trainDataSource.loadDataBlock(mergedData.get());

    /* Create an algorithm object to train the KD-tree based kNN model */
    kdtree_knn_classification::training::Batch<> algorithm;

    /* Pass the training data set and dependent values to the algorithm */
    algorithm.input.set(classifier::training::data, trainData);
    algorithm.input.set(classifier::training::labels, trainGroundTruth);
    algorithm.parameter.nClasses = nClasses;

    /* Train the KD-tree based kNN model */
    algorithm.compute();

    /* Retrieve the results of the training algorithm  */
    trainingResult = algorithm.getResult();
}

void testModel() {
    /* Initialize FileDataSource<CSVFeatureManager> to retrieve the test data from a .csv file */
    FileDataSource<CSVFeatureManager> testDataSource(testDatasetFileName,
                                                     DataSource::notAllocateNumericTable,
                                                     DataSource::doDictionaryFromContext);

    /* Create Numeric Tables for testing data and labels */
    NumericTablePtr testData(new HomogenNumericTable<>(nFeatures, 0, NumericTable::doNotAllocate));
    testGroundTruth = NumericTablePtr(new HomogenNumericTable<>(1, 0, NumericTable::doNotAllocate));
    NumericTablePtr mergedData(new MergedNumericTable(testData, testGroundTruth));

    /* Retrieve the data from input file */
    testDataSource.loadDataBlock(mergedData.get());

    /* Create algorithm objects for KD-tree based kNN prediction with the default method */
    kdtree_knn_classification::prediction::Batch<> algorithm;

    /* Pass the testing data set and trained model to the algorithm */
    algorithm.input.set(classifier::prediction::data, testData);
    algorithm.input.set(classifier::prediction::model,
                        trainingResult->get(classifier::training::model));
    algorithm.parameter.nClasses = nClasses;

    /* Compute prediction results */
    algorithm.compute();

    /* Retrieve algorithm results */
    predictionResult = algorithm.getResult();
}

void printResults() {
    printNumericTables<int, int>(
        testGroundTruth,
        predictionResult->get(kdtree_knn_classification::prediction::prediction),
        "Ground truth",
        "Classification results",
        "KD-tree based kNN classification results (first 20 observations):",
        20);
}
