### 


### Setting up your environment

1. With conda installed, create and activate the environment from `environment.yml`
    - `conda env create -f environment.yml`
    - `conda activate glioma-seg-37`
2. The pipeline uses ANTs to coregister and skull strip. You will need to install this package separately.
    - [Installation instructions](https://andysbrainbook.readthedocs.io/en/latest/ANTs/ANTs_Overview.html)
    - Do not forget to set your ANTSPATH and PATH environment variables (for Linux) as described! 
3. Running the pipeline requires additional reference files you will need to download:
    - The ANTs skull stripping script requires open source brain templates that were released as part of the 2012 MICCAI Multi Atlas Challenge. You can download these templates at [this link](https://figshare.com/articles/dataset/ANTs_ANTsR_Brain_Templates/915436?file=3133832). Place the downloaded files into your `templates/` folder.
    - MSNet weights: 
4. Run `scripts/check_repo_setup.sh` to catch any issues with your file setup in the repository.

### Running the script

1. Your input data for the full pipeline should be raw DICOM files, placed `data/1-input/`
2. `python3 -m src.run_pipeline` will run the pipeline.
3. Output files will be located in the following intermediate data directories:
    - `data/2-nifti/`: perfusion and diffusion NIfTis.
    - `data/3-coreg/`: The coregistered NIfTi T1, T1CE, T2, and flair.
    - `data/5-seg/`: contains NIfTi files of the segmentation masks
    - `data/6-output/`: contains the NIfTi to DICOM conversions of diffusion, perfusion, T1, T1CE, T2, flair, T1CE with mask, flair with mask, and mask.