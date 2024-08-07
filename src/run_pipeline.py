from src.preprocessing.dcm_to_nii import convert_dicom_to_nifti
from src.preprocessing.coreg import coreg
from src.preprocessing.coreg_perf import coreg_perf
from src.preprocessing.skull_strip import skull_strip
from src.models.segmentation import run_msnet_segmentation
from src.postprocessing.postprocess import postprocess
import os
import csv
import time
import stat
from pathlib import Path

def run_pipeline(base_dir):
    """Run the full pipeline, preprocessing, segmentation, postprocessing."""
    start = time.time()
    
    # define intermediate directories
    input_dir = os.path.join(base_dir, '1-input')
    nifti_dir = os.path.join(base_dir, '2-nifti')
    coreg_dir = os.path.join(base_dir, '3-coreg')
    skullstrip_dir = os.path.join(base_dir, '4-skull-strip')
    seg_dir = os.path.join(base_dir, '5-seg')
    output_dir = os.path.join(base_dir, '6-output')

    # convert DICOM files to NIfTi
    if not os.path.exists(nifti_dir):
        os.makedirs(nifti_dir)
        p = Path(nifti_dir)
        p.chmod(p.stat().st_mode | stat.S_IROTH | stat.S_IXOTH | stat.S_IWOTH)
    if len(os.listdir(nifti_dir)) == 0:
        convert_dicom_to_nifti(input_dir, nifti_dir)

    # coregister
    if not os.path.exists(coreg_dir):
        os.makedirs(coreg_dir)
        p = Path(coreg_dir)
        p.chmod(p.stat().st_mode | stat.S_IROTH | stat.S_IXOTH | stat.S_IWOTH)
    if len(os.listdir(coreg_dir)) == 0:
        coreg(nifti_dir, coreg_dir)

    # skull strip
    if not os.path.exists(skullstrip_dir):
        os.makedirs(skullstrip_dir)
        p = Path(skullstrip_dir)
        p.chmod(p.stat().st_mode | stat.S_IROTH | stat.S_IXOTH | stat.S_IWOTH)
    if len(os.listdir(skullstrip_dir)) == 0:
        skull_strip(coreg_dir, skullstrip_dir)

    #register skull stripped t1ce and perfusion map
    coreg_perf(nifti_dir, coreg_dir, skullstrip_dir)

    # glioma segmentation
    if not os.path.exists(seg_dir):
        os.makedirs(seg_dir)
        p = Path(seg_dir)
        p.chmod(p.stat().st_mode | stat.S_IROTH | stat.S_IXOTH | stat.S_IWOTH)
    if len(os.listdir(seg_dir)) == 0:
        tumor_volume = run_msnet_segmentation(skullstrip_dir, seg_dir)
    else:
        # read tumor volume from file
        tumor_volume = {}
        with open(os.path.join(seg_dir, "tumor_volume.csv")) as f:
            reader = csv.reader(f)
            for row in reader:
                tumor_volume[row[0]] = row[1]

    # nifti to dicom
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        p = Path(output_dir)
        p.chmod(p.stat().st_mode | stat.S_IROTH | stat.S_IXOTH | stat.S_IWOTH)
    if len(os.listdir(output_dir)) == 0:
        # select a DICOM file to use as a template
        dcm_source_file = os.listdir(input_dir)[0]
        dcm_source_file = os.path.join(input_dir, dcm_source_file)
        print("postprocessing started")
        postprocess(nifti_dir, coreg_dir, seg_dir, output_dir, dcm_source_file, tumor_volume)

    #set permissions for output files
    for root, dirs, files in os.walk(output_dir):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o777)
        for f in files:
            os.chmod(os.path.join(root, f), 0o777)

    end = time.time()

    print("DONE")
    print("RUNTIME:", end - start)

if __name__ == "__main__":
    #run_pipeline("/home/amritha/workspace/coreg-skull-strip-testing/data/")
    #run_pipeline("/home/vagrant/MSNet-pipeline/data/")
    run_pipeline("/data/")
