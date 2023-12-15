from pathlib import Path
import os
import csv

from src.models.msnet.inference import run_inference

def run_msnet_segmentation(input_dir, output_dir):
    
    if not os.path.exists(os.path.join(input_dir, "patient")):
        os.makedirs(os.path.join(input_dir, "patient"))
    os.system(f"mv {input_dir}/*.nii.gz {input_dir}/patient/")

    config_file = Path("src/models/msnet/config/mercure_config.txt")

    tumor_volume = run_inference(input_dir, output_dir, config_file)

    os.system(f"mv {input_dir}/patient/*.nii.gz {input_dir}/")

    os.system(f"mv {output_dir}/patient/patient_seg_edema.nii.gz {output_dir}/seg_edema.nii.gz")
    os.system(f"mv {output_dir}/patient/patient_seg_enhanced.nii.gz {output_dir}/seg_enhanced.nii.gz")
    os.system(f"mv {output_dir}/patient/patient_seg_non_enhanced.nii.gz {output_dir}/seg_non_enhanced.nii.gz")
    os.system(f"mv {output_dir}/patient/patient_seg_whole.nii.gz {output_dir}/seg_whole.nii.gz")
    os.system(f"rm {output_dir}/patient/tumor_volume.txt")

    os.system(f"rm {output_dir}/test_time.txt")
    os.system(f"rm -rf {input_dir}/patient/")
    os.system(f"rm -rf {output_dir}/patient/")

    # save tumor volume to file
    with open(f"{output_dir}/tumor_volume.csv", "w") as f:
        writer = csv.writer(f)
        for key, val in tumor_volume.items():
            writer.writerow([key, val])

    return tumor_volume
