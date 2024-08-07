import os
import stat
from pathlib import Path
import shutil

def ants_coreg(fixed_nifti, moving_nifti, setting):
    """Coregister two NIfTI files using ANTs.

    Args:
        fixed_nifti: Path to fixed NIfTI file
        moving_nifti: Path to moving NIfTI file
        setting: forproduction or fastfortesting
    """
    # run ants registration script
    os.system("scripts/ants_coreg.sh {} {} {}".format(fixed_nifti, moving_nifti, setting))


def coreg_perf(nifti_dir, coreg_dir, skullstrip_dir):
    """Coregister modalities needed for segmentation to T1c using ANTs.

    Args:
        nifti_dir: Directory containing NIfTI files
        coreg_dir: Directory where coregistered NIfTI files will be placed
    """
    # get list of modalities
    modality = 'perfusion'

    # coregister perfusion modality to T1ce
    
    fixed_nifti = os.path.join(skullstrip_dir, 'brain_t1ce.nii.gz')
    moving_nifti = os.path.join(nifti_dir, f'brain_{modality}.nii.gz')
    ants_coreg(fixed_nifti, moving_nifti, 'fastfortesting')

    # move coregistered file to coreg_dir and skull_strip dir
    registered_nifti = [file for file in os.listdir('.') if modality in file and file.endswith('_warped.nii.gz')][0]
    new_file_path = os.path.join(coreg_dir, f'brain_{modality}.nii.gz')
    os.rename(registered_nifti, new_file_path)
    p = Path(new_file_path)
    p.chmod(p.stat().st_mode | stat.S_IROTH | stat.S_IXOTH | stat.S_IWOTH)

    # Copy the renamed file to the skullstripe_dir directory
    shutil.copy(new_file_path, skullstrip_dir)
    s_dir_path = os.path.join(skullstrip_dir, f'brain_{modality}.nii.gz')
    p = Path(s_dir_path)
    p.chmod(p.stat().st_mode | stat.S_IROTH | stat.S_IXOTH | stat.S_IWOTH)

    

    # remove intermediate files
    os.system("rm *.nii.gz")
    os.system("rm *.mat")
