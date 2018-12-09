# To build and publish image run following commands:
# > docker build -t cahirwpz/demoscene-toolchain:latest .
# > docker login
# > docker push cahirwpz/demoscene-toolchain:latest

FROM debian:stretch

WORKDIR /root

RUN apt-get -q update && apt-get upgrade -y
RUN apt-get install -y --no-install-recommends libc6-i386
ADD http://circleci.com/api/v1/project/cahirwpz/demoscene-toolchain/latest/artifacts/0/root/demoscene-toolchain/demoscene-toolchain.tar.gz demoscene-toolchain.tar.gz
RUN tar -C / -xvzf demoscene-toolchain.tar.gz && rm demoscene-toolchain.tar.gz
