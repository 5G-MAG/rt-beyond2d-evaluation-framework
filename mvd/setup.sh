#!/bin/bash
# --------------------------------------------------------------------------------
# Copyright © 2025, Koninklijke Philips N.V.
#
# Licensed under the License terms and conditions for use, reproduction, and
# distribution of 5G-MAG software (the “License”).  You may not use this file
# except in compliance with the License.  You may obtain a copy of the License at
# https://www.5g-mag.com/reference-tools.  Unless required by applicable law or
# agreed to in writing, software distributed under the License is distributed on
# an “AS IS” BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied.
#
# See the License for the specific language governing permissions and limitations
# under the License.
# --------------------------------------------------------------------------------

set -e

TMIV_TAG=v24.0
QMIV_TAG=v2.0-rc

if [ "$1" == "--help" ]
then
    echo "Usage: setup.sh [--system]"
    exit 1
fi

# Install required system packages
if [ "$1" == "--system" ]
then
    shift
    sudo apt update
    sudo apt upgrade -y
    sudo apt install -y --no-install-recommends \
        build-essential \
        clang \
        git \
        libc++-dev \
        libclang-rt-dev \
        llvm \
        python3-pip \
        python3-venv
fi

# Set-up a Python virtual environment
python3 -m venv venv
. venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

# Set-up C++ toolchain
export CC=clang
export CXX=clang++
export CFLAGS=
export CXXFLAGS="-stdlib=libc++"
export LDFLAGS="-stdlib=libc++ -rtlib=compiler-rt -fuse-ld=lld -ldl -Wl,--undefined-version"

# Clone TMIV
[ -d "$PWD/.deps/tmiv-$TMIV_TAG" ] || \
    git clone https://gitlab.com/mpeg-i-visual/tmiv.git -b $TMIV_TAG .deps/tmiv-$TMIV_TAG

# Clone QMIV
[ -d "$PWD/.deps/qmiv-$QMIV_TAG" ] || \
    git clone https://gitlab.com/mpeg-i-visual/qmiv.git -b $QMIV_TAG .deps/qmiv-$QMIV_TAG

# Configure, build and install TMIV and dependencies
python .deps/tmiv-$TMIV_TAG/scripts/install.py \
    clang-release \
    --dependencies-source-dir $PWD/.deps \
    --install-prefix $PWD/tmiv

# Configure, build and install QMIV
cmake -G Ninja -S .deps/qmiv-$QMIV_TAG -B .deps/qmiv-$QMIV_TAG/build -DCMAKE_BUILD_TYPE=Release \
    -DPMBB_GENERATE_MULTI_MICROARCH_LEVEL_BINARIES:BOOL=True \
    -DPMBB_GENERATE_SINGLE_APP_WITH_WITH_RUNTIME_DISPATCH:BOOL=True
ninja -C .deps/qmiv-$QMIV_TAG/build
ln -s .deps/qmiv-$QMIV_TAG/build/QMIV/QMIV qmiv
