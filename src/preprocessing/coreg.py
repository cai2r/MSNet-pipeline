import os
import stat
from pathlib import Path

def ants_coreg(fixed_nifti, moving_nifti, setting):
    """Coregister two NIfTI files using ANTs.

    Args:
        fixed_nifti: Path to fixed NIfTI file
        moving_nifti: Path to moving NIfTI file
        setting: forproduction or fastfortesting
    """
    # run ants registration script
    os.system("scripts/ants_coreg.sh {} {} {}".format(fixed_nifti, moving_nifti, setting))


def coreg(nifti_dir, coreg_dir):
    """Coregister modalities needed for segmentation to T1c using ANTs.

    Args:
        nifti_dir: Directory containing NIfTI files
        coreg_dir: Directory where coregistered NIfTI files will be placed
    """
    # get list of modalities
    modalities = ['t1', 't1ce', 't2', 'flair']

    # coregister each modality to T1ce
    for modality in modalities:
        if modality == 't1ce':
            os.system(f"cp {os.path.join(nifti_dir, 'brain_t1ce.nii.gz')} {os.path.join(coreg_dir, 'brain_t1ce.nii.gz')}")
            p = Path(os.path.join(coreg_dir, 'brain_t1ce.nii.gz'))
            p.chmod(p.stat().st_mode | stat.S_IROTH | stat.S_IXOTH | stat.S_IWOTH)
        else:
            fixed_nifti = os.path.join(nifti_dir, 'brain_t1ce.nii.gz')
            moving_nifti = os.path.join(nifti_dir, f'brain_{modality}.nii.gz')
            ants_coreg(fixed_nifti, moving_nifti, 'fastfortesting')

            # move coregistered file to coreg_dir
            registered_nifti = [file for file in os.listdir('.') if modality in file and file.endswith('_warped.nii.gz')][0]
            os.rename(registered_nifti, os.path.join(coreg_dir, f'brain_{modality}.nii.gz'))
            p = Path(os.path.join(coreg_dir, f'brain_{modality}.nii.gz'))
            p.chmod(p.stat().st_mode | stat.S_IROTH | stat.S_IXOTH | stat.S_IWOTH)

            # remove intermediate files
            os.system("rm *.nii.gz")
            os.system("rm *.mat")
