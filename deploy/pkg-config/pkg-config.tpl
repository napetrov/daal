#===============================================================================
# Copyright 2021 Intel Corporation
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

prefix=${{pcfiledir}}/../../
exec_prefix=${{prefix}}
libdir=${{exec_prefix}}/{libdir}
includedir=${{prefix}}/include

#info
Name: oneDAL
Description: oneAPI Data Analytics Library
Version: 2025.8
URL: https://www.intel.com/content/www/us/en/developer/tools/oneapi/onedal.html
#Link line
Libs: {libs}
#Compiler line
Cflags: {opts}
