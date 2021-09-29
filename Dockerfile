# To build and publish image run following commands:
# > docker build -t cahirwpz/demoscene-toolchain:latest .
# > docker login
# > docker push cahirwpz/demoscene-toolchain:latest

FROM debian:bullseye-backports

WORKDIR /root

RUN apt-get -q update && apt-get upgrade -y
RUN apt-get install -y --no-install-recommends \
            automake bison ca-certificates flex git-core gettext gperf \
            gcc g++ libc6-dev libglib2.0-dev libncurses-dev libpng-dev \
            libsdl2-dev libopenal-dev libtool make patch pkg-config \
            python3 libpython3-dev python3-setuptools quilt \
            subversion texinfo zip
