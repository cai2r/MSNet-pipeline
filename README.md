# MSNet-pipeline

### About
The MSNet-pipeline project provides a pipeline for executing the MSNet model [1] on brain MRI exams. The project provides options for locally running and container execution.

### Pipeline Structure

1. **DICOM to NIfTi Conversion**: The pipeline converts DICOM files in `data/1-input/` to NIfTi files and places them in `data/2-nifti`. T1CE, T1, T2, and Flair modalities are kept, if DWI (b-1000) and perfusion are available, those are also selected.
2. **Coregistration**: The T1, T2, and Flair modalities are coregistered (using the ANTs package) to T1CE. Coregistered NIfTi files are placed in `data/3-coreg`.
3. **Skull Stripping**: The T1CE, T1, T2, and Flair modalities are skull stripped and placed in `data/4-skull-strip`.
4. **Glioma Segmentation**: The T1CE, T1, T2, and Flair NIfTi's in `data/4-skull-strip` are passed to the MSNet model. The output is another set of NIfTI files containing the three masks as expected in the BraTS challenge (Whole Tumor, Tumor Core and Enhancing Tumor). Output segmentations are placed in `data/5-seg`
5. **Postprocessing**: Since the final prediction is expected to be saved in the PACS filesystem, the final outputs are DICOM files that contain the predicted segmentation mask on top of the original images, placed in `data/6-output`. DWI and perfusion (if found), T1, T1CE, T2, and Flair are converted back to DICOM. The whole segmentation mask is converted back to DICOM. Finally, Flair and T1CE volumes, with the whole segmentation mask overlaid on them, are also converted.

## Getting Started
### Setting up your environment

1. With conda installed, create and activate the environment from `environment.yml`
    - `conda env create -f environment.yml`
    - `conda activate glioma-seg-37`
2. The pipeline uses ANTs to coregister and skull strip. You will need to install this package separately.
    - [Installation instructions](https://andysbrainbook.readthedocs.io/en/latest/ANTs/ANTs_Overview.html)
    - Do not forget to set your ANTSPATH and PATH environment variables (for Linux) as described! 
3. Running the pipeline requires additional reference files you will need to download:
    - The ANTs skull stripping script requires open source brain templates that were released as part of the 2012 MICCAI Multi Atlas Challenge. You can download these templates at [this link](https://figshare.com/articles/dataset/ANTs_ANTsR_Brain_Templates/915436?file=3133832). Place the downloaded files into your `templates/` folder.
    - MSNet weights: ask a team member for the correct MSNet weights, and place these into the `src/models/msnet/model19_prepost4s/` folder.
4. Run `scripts/check_repo_setup.sh` to catch any issues with your file setup in the repository.
5. It may be necessary to copy the /src/build_tools/misc_io.py file over to your new environment, and reinstall correct tensorflow-gpu version (see Dockerfile for correct commands).

### Running the pipeline

1. Your input data for the full pipeline should be raw DICOM files, placed `data/1-input/`
2. `python3 -m src.run_pipeline` will run the pipeline.
3. Output files will be located in the following intermediate data directories:
    - `data/2-nifti/`: perfusion and diffusion NIfTis.
    - `data/3-coreg/`: The coregistered NIfTi T1, T1CE, T2, and flair.
    - `data/5-seg/`: contains NIfTi files of the segmentation masks
    - `data/6-output/`: contains the NIfTi to DICOM conversions of diffusion, perfusion, T1, T1CE, T2, flair, T1CE with mask, flair with mask, and mask. (An easy tool to view these DICOM files is [Weasis](https://weasis.org/en/index.html))

## Citations

1. Lotan E, Zhang B, Dogra S, et al. **Development and Practical Implementation of a Deep Learning-Based Pipeline for Automated Pre- and Postoperative Glioma Segmentation.** *AJNR Am J Neuroradiol. 2022;43(1):24-32.* https://doi.org/10.3174/ajnr.A7363
2. Isensee, F., Jaeger, P.F., Kohl, S.A.A. et al. **nnU-Net: a self-configuring method for deep learning-based biomedical image segmentation.** *Nat Methods 18, 203–211 (2021).* https://doi.org/10.1038/s41592-020-01008-z

