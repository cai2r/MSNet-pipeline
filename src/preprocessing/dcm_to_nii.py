import os
import sys
import json
from pathlib import Path
from src.common.enums import modalities
import nibabel as nib


def set_modalities(in_folder, modalities=modalities):
    # Load the task.json file, which contains the settings for the processing module
    settings={}
    try:
        with open(Path(in_folder) / "task.json", "r") as json_file:
            task = json.load(json_file)
    except Exception:
        print("Error: Task file task.json not found")
        sys.exit(1)
     # Overwrite default modalities values with settings from the task file (if present)
    if task.get("process", ""):
        settings.update(task["process"].get("settings", {}))
    # Get dcm2bids config and write configuration file
    print(settings)
    print(type(settings))
    if "modalities" in settings:
        print("user specified modalities found")
        modalities_selected = settings["modalities"]
    else:
        print("No user specified modalities found, running with default values")
        modalities_selected = modalities
    return modalities_selected

def dcm2niix_wrapper(dcm_dir, nii_dir):
    """Converts DICOM files to NIfTI using dcm2niix.

    Args:
        dcm_dir: Directory containing DICOM input files
        nii_dir: Directory where four NIfTI files corresponding to brain MRI
            modalities will be placed

    """
    # check that dcm_dir is a valid directory
    if not os.path.isdir(dcm_dir):
        raise ValueError(f"Dataset directory {dcm_dir} does not exist")

    # run conversion
    print("Start to compress DICOM to NIfTI files...")
    os.system("dcm2niix -o {} -z y {}".format(nii_dir, dcm_dir))


def select_diffusion_file(nii_dir, bval=1000):
    """Select diffusion modality based on bval file."""
    for file in os.listdir(nii_dir):
        if ".bval" in file:
            with open(os.path.join(nii_dir, file)) as f:
                bvals = f.read().split()
                bvals = [int(bval) for bval in bvals]
                if bval in bvals:
                    return [file.replace(".bval", ".nii.gz")]
    return []


def remove_nonstandard_modalities(nii_dir):
    """Remove nifti files that are not the specified modalities.

    Args:
        nii_dir: Directory containing NIfTI files

    """
    # remove analysis and computed files that do not have desired data format
    os.system("rm {}/*fMRI*".format(nii_dir))
    os.system("rm {}/*ROI*".format(nii_dir))
    os.system("rm {}/*OLEA*".format(nii_dir))

    # remove files that are not standard modalities
    os.system("rm {}/*SCOUT*".format(nii_dir))
    os.system("rm {}/*SWI*".format(nii_dir))


def select_necessary_modalities(nii_dir, modalities=modalities):
    """Remove nifti files that are not the specified modalities.

    Args:
        nii_dir: Directory containing NIfTI files
        modalities: Dictionary containing the modalities to keep, keys are the
            modalities and values are valid substrings for the filenames

    """
    # save off all files
    os.makedirs(os.path.join(nii_dir, "all"), exist_ok=True)
    os.system(f"cp {nii_dir}/*.nii.gz {nii_dir}/all")

    # get list of files for each modality
    files_per_modality = {}
    for mod in modalities.keys():
        if mod == "diffusion":
            files_per_modality[mod] = select_diffusion_file(nii_dir, bval=1000)
            if len(files_per_modality[mod]) == 0:
                files_per_modality[mod] = select_diffusion_file(nii_dir, bval=1500)
        else:
            files_per_modality[mod] = []
            for pattern in modalities[mod]:
                for file in os.listdir(nii_dir):
                    if (pattern in file) and (".nii.gz" in file):
                        files_per_modality[mod].append(file)
                if len(files_per_modality[mod]) > 0:
                    break

    mod_niftis = []
    for mod in files_per_modality.keys():
        if len(files_per_modality[mod]) > 0:
            mod_name = "brain_" + mod + ".nii.gz"
            mod_niftis.append(mod_name)

            # pick the file with the shortest suffix
            suffixes_to_check = [file.split('.')[0] for file in files_per_modality[mod]]
            suffixes_to_check = [file.split('_')[-1] for file in suffixes_to_check]

            trailing_numbers = [int(s) for s in suffixes_to_check if not s[-1].isalpha()]
            trailing_numbers = sorted(trailing_numbers)

            for num in trailing_numbers:
                nifti_to_keep = [file for file in files_per_modality[mod] if str(num)+"." in file][0]
                
                # check that the file exists and is 3D
                if os.path.isfile(os.path.join(nii_dir, nifti_to_keep)):
                    if int(nib.load(os.path.join(nii_dir, nifti_to_keep)).header["dim"][4]) > 1:
                        break

            os.system(f"mv {nii_dir}/{nifti_to_keep} {nii_dir}/{mod_name}")
        else:
            print(f"WARNING: No files found for modality {mod}")

    # remove files that are not the specified modalities
    for file in os.listdir(nii_dir):
        if file not in mod_niftis and os.path.isfile(os.path.join(nii_dir, file)):
            os.remove(os.path.join(nii_dir, file))


def convert_dicom_to_nifti(dcm_dir, nii_dir):
    """Convert DICOM files to NIfTI.

    Args:
        dcm_dir: Directory containing DICOM input files
        nii_dir: Directory where four NIfTI files corresponding to brain MRI
            modalities will be placed

    """
    # check task file for user setting of modalities
    specified_modalities = set_modalities(dcm_dir)
    # convert DICOM files to NIfTI
    dcm2niix_wrapper(dcm_dir, nii_dir)
    remove_nonstandard_modalities(nii_dir)
    select_necessary_modalities(nii_dir, specified_modalities)
