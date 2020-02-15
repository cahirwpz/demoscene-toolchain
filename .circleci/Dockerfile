# To build and publish image run following commands:
# > docker build -t cahirwpz/demoscene-toolchain-buildenv:latest .
# > docker login
# > docker push cahirwpz/demoscene-toolchain-buildenv:latest

FROM debian:buster

WORKDIR /root

RUN apt-get -q update && apt-get upgrade -y
RUN apt-get install -y --no-install-recommends \
            git-core make gettext patch bison flex gperf ca-certificates \
            gcc g++ gcc-multilib libc6-dev libncurses-dev \
            python3 libpython3-dev python3-setuptools quilt subversion texinfo
