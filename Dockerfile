# To build and publish image run following commands:
# > docker image build -t cahirwpz/demoscene-toolchain:ubuntu-26.04 .
# > docker login
# > docker push cahirwpz/demoscene-toolchain:ubuntu-26.04

FROM ubuntu:26.04

WORKDIR /root

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -q update && apt-get upgrade -y
RUN apt-get install -y --no-install-recommends \
            automake autoconf bison ca-certificates flex gcc g++ gettext git \
            gperf libc6-dev libglib2.0-dev libncurses-dev libopenal-dev \
            libpng-dev libsdl2-dev libsdl2-ttf-dev libtool make patch perl \
            pkg-config python3 python3-dev python3-venv quilt texinfo zip \
            debhelper fakeroot
