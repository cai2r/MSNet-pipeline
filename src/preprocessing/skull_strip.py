import os
import nibabel as nib

def ants_skull_strip(image, coreg_dir, skullstrip_dir):
    # define paths
    template_path = "templates/MICCAI2012-Multi-Atlas-Challenge-Data/"
    image_file = os.path.join(coreg_dir, image)
    brain_with_skull_template = template_path + "T_template0.nii.gz"
    brain_prior = template_path + "T_template0_BrainCerebellumProbabilityMask.nii.gz"
    registration_mask = template_path + "T_template0_BrainCerebellumRegistrationMask.nii.gz"
    output_prefix = "stripped"

    # run ants skull stripping script
    os.system("scripts/ants_skull_strip.sh -d 3 -a {} \
              -e {} \
              -m {} \
              -o {}".format(image_file, brain_with_skull_template, brain_prior, output_prefix))

    # move output files to skullstrip_dir
    os.system("mv *Brain.nii.gz {}/{}".format(skullstrip_dir, image))


def apply_mask(coreg_dir, skullstrip_dir, image, mask):
    """Apply the brain segmentation mask to the input image."""
    # Load NIfTI files
    image_file = os.path.join(coreg_dir, image)
    nifti_input_image = nib.load(image_file)
    nifti_mask_image = nib.load(mask)

    # Apply mask
    masked_image_data = nifti_input_image.get_fdata() * nifti_mask_image.get_fdata()

    # Create new NIfTI file
    nifti_mask_image = nib.nifti1.Nifti1Image(
        masked_image_data,
        affine=nifti_input_image.affine,
        header=nifti_input_image.header,
    )

    # Save NIfTI file
    output_filename = os.path.join(skullstrip_dir, image)
    nib.save(nifti_mask_image, output_filename)


def skull_strip(coreg_dir, skullstrip_dir):
    """Skull strip modalities needed for segmentation using ANTs.

    Args:
        coreg_dir: Directory containing coregistered NIfTI files
        skullstrip_dir: Directory where skull stripped NIfTI files will be placed
    """
    # modalities to skull strip
    modalities = ['t1ce', 't1', 't2', 'flair']

    # skull strip T1CE
    image = 'brain_t1ce.nii.gz'
    ants_skull_strip(image, coreg_dir, skullstrip_dir)
    mask_file = f'strippedBrainExtractionMask.nii.gz'
    
    # apply mask to remaining modalities
    for modality in modalities:
        image = f'brain_{modality}.nii.gz'
        apply_mask(coreg_dir, skullstrip_dir, image, mask_file)

    # remove intermediate files
    os.system("rm *BrainExtraction*")
