FROM ubuntu:bionic-20220427
#as builder

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

RUN wget --quiet -O - https://apt.kitware.com/keys/kitware-archive-latest.asc 2>/dev/null \
    | apt-key add - \
  && apt-add-repository -y 'deb https://apt.kitware.com/ubuntu/ bionic main' \
  && apt-get update \
  && apt-get -y install cmake=3.18.3-0kitware1 cmake-data=3.18.3-0kitware1


ADD . /tmp/ants/source

RUN git clone https://github.com/ANTsX/ANTs.git


RUN cp -r ./ANTs/* /tmp/ants/source


#ARG BUILD_SHARED_LIBS=ON

RUN mkdir -p /tmp/ants/build \
    && cd /tmp/ants/build \
    && mkdir -p /opt/ants \
    && git config --global url."https://".insteadOf "git://" \
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

#FROM ubuntu:bionic-20220427
#COPY --from=builder /opt/ants /opt/ants
#COPY --from=builder /opt/ants /opt/ants

ADD . /
RUN chmod -R 777 /data
RUN chmod -R 777 /scripts
RUN chmod -R 777 /src
RUN chmod -R 777 /templates
RUN chmod -R 777 /environment.yml

RUN apt-get update && apt-get install --no-install-recommends --no-install-suggests -y git build-essential cmake pigz
RUN apt-get update && apt-get install --no-install-recommends --no-install-suggests -y libsm6 libxrender-dev libxext6 ffmpeg 
RUN apt-get install unzip
RUN apt-get install -y wget

RUN wget --quiet -O /tmp/miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
# install miniconda
ARG CONDA_DIR=/opt/conda
ENV PATH $CONDA_DIR/bin:$PATH
RUN bash /tmp/miniconda.sh -b -p $CONDA_DIR
RUN rm -rf /tmp/*


RUN conda create -n env python=3.7
RUN echo "source activate env" > ~/.bashrc
ENV PATH /opt/conda/envs/env/bin:$PATH
RUN chmod -R 777 /opt/conda/envs

RUN conda env create -f ./environment.yml

# Pull the environment name out of the environment.yml
RUN echo "source activate $(head -1 ./environment.yml | cut -d' ' -f2)" > ~/.bashrc
#ENV PATH /opt/conda/envs/$(head -1 ./environment.yml | cut -d' ' -f2)/bin:$PATH
ENV PATH /opt/conda/envs/$(head -1 ./environment.yml | cut -d' ' -f2)/bin:$PATH

LABEL maintainer="ANTsX team" \
      description="ANTs is part of the ANTsX ecosystem (https://github.com/ANTsX). \
ANTs Citation: https://pubmed.ncbi.nlm.nih.gov/24879923"

ENV PATH="/opt/ants/bin:$PATH" \
    LD_LIBRARY_PATH="/opt/ants/lib:$LD_LIBRARY_PATH"
RUN apt-get update \
    && apt install -y --no-install-recommends bc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ADD ./src/build_tools/misc_io.py /opt/conda/envs/glioma-seg-37/lib/python3.7/site-packages/niftynet/io/misc_io.py
# manage niftynet specific set up issues
RUN mkdir /.niftynet && chmod -R 777 /.niftynet \
    && mkdir /niftynet && chmod -R 777 /niftynet


# run entrypoint with conda environment
RUN chmod 777 /scripts/docker-entrypoint.sh && \
    chmod -R 777 /src/models/msnet/model19_prepost4s/

RUN pip3 uninstall protobuf
#RUN pip3 install --user protobuf==3.20
RUN pip3 install protobuf==3.20
RUN pip3 uninstall tensorflow-gpu tensorflow
#RUN pip3 install --user tensorflow-gpu~=1.12
RUN pip3 install tensorflow-gpu~=1.12


CMD ["/scripts/docker-entrypoint.sh"]
