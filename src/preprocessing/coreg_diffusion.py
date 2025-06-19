import os
import stat
from pathlib import Path
import shutil

def ants_coreg(fixed_nifti, moving_nifti):
    """Coregister two NIfTI files using ANTs.

    Args:
        fixed_nifti: Path to fixed NIfTI file
        moving_nifti: Path to moving NIfTI file
    """
    # run ants registration script
    output_prefix = 'output_diffusion_'
    command = f"scripts/antsRegistrationSyN.sh -d 3 -n 8 -t r -f {fixed_nifti} -m {moving_nifti} -o {output_prefix}"
    os.system(command)


def coreg_diffusion(nifti_dir, coreg_dir):
    """Coregister diffusion data to T2 using ANTs.

    Args:
        nifti_dir: Directory containing NIfTI files
        coreg_dir: Directory where coregistered NIfTI files will be placed
    """
    # get list of modalities
    modality = 'diffusion'

    # coregister perfusion modality to T1ce    
    fixed_nifti = os.path.join(coreg_dir, 'brain_t1ce.nii.gz')
    moving_nifti = os.path.join(nifti_dir, f'brain_{modality}.nii.gz')
    ants_coreg(fixed_nifti, moving_nifti)

    # move coregistered file to coreg_dir and skull_strip dir
    registered_nifti = [file for file in os.listdir('.') if file.endswith('output_diffusion_Warped.nii.gz')][0]
    new_file_path = os.path.join(coreg_dir, f'brain_{modality}.nii.gz')
    os.rename(registered_nifti, new_file_path)
    p = Path(new_file_path)
    p.chmod(p.stat().st_mode | stat.S_IROTH | stat.S_IXOTH | stat.S_IWOTH)

    # remove intermediate files
    os.system("rm *.nii.gz")
    os.system("rm *.mat")
