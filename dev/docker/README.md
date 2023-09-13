<!--
******************************************************************************
* Copyright 2023 Intel Corporation
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
*******************************************************************************/-->

# Docker dev environemnt
## How to use
This is simple docker dev environment intended for oneDAL development and build process.
It does include dependencies for building all oneDAL components through both make and bazel

Note: docker setup assumes that it's executed from oneDAL checkouted repo and copy repo files inside container

Just run:
   ```sh
   docker run -it onedal-dev /bin/bash
   ```