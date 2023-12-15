FROM ubuntu:bionic-20220427 as builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
                    apt-transport-https \
                    bc \
                    build-essential \
                    ca-certificates \
                    gnupg \
                    ninja-build \
                    git \
                    software-properties-common \
                    wget

RUN wget -O - https://apt.kitware.com/keys/kitware-archive-latest.asc 2>/dev/null \
    | apt-key add - \
  && apt-add-repository -y 'deb https://apt.kitware.com/ubuntu/ bionic main' \
  && apt-get update \
  && apt-get -y install cmake=3.18.3-0kitware1 cmake-data=3.18.3-0kitware1

ADD . /tmp/ants/source
RUN mkdir -p /tmp/ants/build \
    && cd /tmp/ants/build \
    && mkdir -p /opt/ants \
    && git config --global url."https://".insteadOf git:// \
    && cmake \
      -GNinja \
      -DBUILD_TESTING=ON \
      -DRUN_LONG_TESTS=OFF \
      -DRUN_SHORT_TESTS=ON \
      -DBUILD_SHARED_LIBS=ON \
      -DCMAKE_INSTALL_PREFIX=/opt/ants \
      /tmp/ants/source \
    && cmake --build . --parallel \
    && cd ANTS-build \
    && cmake --install .

# Need to set library path to run tests
ENV LD_LIBRARY_PATH="/opt/ants/lib:$LD_LIBRARY_PATH"

RUN cd /tmp/ants/build/ANTS-build \
    && cmake --build . --target test

FROM ubuntu:bionic-20220427
COPY --from=builder /opt/ants /opt/ants

LABEL maintainer="ANTsX team" \
      description="ANTs is part of the ANTsX ecosystem (https://github.com/ANTsX). \
ANTs Citation: https://pubmed.ncbi.nlm.nih.gov/24879923"

ENV PATH="/opt/ants/bin:$PATH" \
    LD_LIBRARY_PATH="/opt/ants/lib:$LD_LIBRARY_PATH"
RUN apt-get update \
    && apt install -y --no-install-recommends bc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# copy working directory with model code into image
COPY . ./

# install miniconda
ARG CONDA_DIR=/opt/miniconda
ENV PATH $CONDA_DIR/bin:$PATH
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    bash /tmp/miniconda.sh -b -p $CONDA_DIR && \
    rm -rf /tmp/*

# create conda env based on our environment file
RUN $CONDA_DIR/bin/conda env create -f environment.yml

# manage niftynet specific set up issues
RUN cp ./src/build_tools/misc_io.py /opt/miniconda/envs/glioma-seg-37/lib/python3.7/site-packages/niftynet/io/misc_io.py && \
    mkdir /.niftynet && chmod -R 777 /.niftynet && \
    mkdir /niftynet && chmod -R 777 /niftynet

# run entrypoint with conda environment
RUN chmod 777 ./scripts/docker-entrypoint.sh && \
    chmod -R 777 /models/msnet/model19_prepost4s/
ENTRYPOINT ["conda", "run", "-n", "glioma-seg-37", "/scripts/docker-entrypoint.sh"]
