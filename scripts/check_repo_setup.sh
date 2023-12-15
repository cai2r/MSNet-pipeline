#!/usr/bin/env bash
DATA_DIR=data
if [ ! -d "$DATA_DIR" ]; then
    mkdir data/
    mkdir data/1-input/
    mkdir data/2-nifti/
    mkdir data/3-coreg/
    mkdir data/4-skull-strip/
    mkdir data/5-seg/
    mkdir data/6-output/
fi

TEMPLATE_DIR=templates
MICCAI_TEMPLATE_DIR=$TEMPLATE_DIR/MICCAI2012-Multi-Atlas-Challenge-Data
if [ ! -d "$TEMPLATE_DIR" ]; then
    mkdir templates/
fi
if [ ! -d "$MICCAI_TEMPLATE_DIR" ]; then
    echo "$MICCAI_TEMPLATE_DIR does not exist. \
            You will need to download templates from https://figshare.com/articles/dataset/ANTs_ANTsR_Brain_Templates/915436?file=3133832 \
            and place the files into $MICCAI_TEMPLATE_DIR"
fi

WEIGHTS_DIR=src/models/msnet/model19_prepost4s
if [ ! -d "$WEIGHTS_DIR" ]; then
    echo "$WEIGHTS_DIR does not exist. \
            You will need to download the MSNet weights \
            and place the files into $WEIGHTS_DIR"
fi
