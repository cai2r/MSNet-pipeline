from src.preprocessing.dcm_to_nii import convert_dicom_to_nifti
from src.preprocessing.coreg import coreg
from src.preprocessing.coreg_perf import coreg_perf
from src.preprocessing.coreg_diffusion import coreg_diffusion
from src.preprocessing.skull_strip import skull_strip
from src.models.segmentation import run_msnet_segmentation
from src.postprocessing.postprocess import postprocess
import os, csv, time, stat, glob
from pathlib import Path
from pydicom import dcmread


def run_pipeline(base_dir):
    """Run the full pipeline, preprocessing, segmentation, postprocessing."""
    start = time.time()
    print("### Starting pipeline...")

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
        print("### Converting to NIfTI...")
        convert_dicom_to_nifti(input_dir, nifti_dir)
    else:
        print("### Skipping NIfTY conversion...")

    # coregister
    if not os.path.exists(coreg_dir):
        os.makedirs(coreg_dir)
        p = Path(coreg_dir)
        p.chmod(p.stat().st_mode | stat.S_IROTH | stat.S_IXOTH | stat.S_IWOTH)
    if len(os.listdir(coreg_dir)) == 0:
        print("### Running coregistration...")
        coreg(nifti_dir, coreg_dir) # data is coregistered to T1CE using transforms: rigid + affine
        coreg_diffusion(nifti_dir, coreg_dir) # diffusion data is coregistered to T2 using transforms: rigid + affine + deformable syn (3 stages)
    else:
        print("### Skipping coregistration...")

    # skull strip
    if not os.path.exists(skullstrip_dir):
        os.makedirs(skullstrip_dir)
        p = Path(skullstrip_dir)
        p.chmod(p.stat().st_mode | stat.S_IROTH | stat.S_IXOTH | stat.S_IWOTH)
    if len(os.listdir(skullstrip_dir)) == 0:
        print("### Running skullstripping...")
        skull_strip(coreg_dir, skullstrip_dir)
        coreg_perf(nifti_dir, coreg_dir, skullstrip_dir) # data is coregistered to skull-stripped T1CE using transforms: rigid 
    else:
        print("### Skipping skullstripping...")

    # glioma segmentation
    if not os.path.exists(seg_dir):
        os.makedirs(seg_dir)
        p = Path(seg_dir)
        p.chmod(p.stat().st_mode | stat.S_IROTH | stat.S_IXOTH | stat.S_IWOTH)
    if len(os.listdir(seg_dir)) == 0:
        print("### Running segmentation...")
        tumor_volume = run_msnet_segmentation(skullstrip_dir, seg_dir)
    else:
        print("### Skipping segmentation...")
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
        print("### Running postprocessing...")
        # select a DICOM file to use as a template
        dcm_source_file = glob.glob(input_dir+'/*.dcm')[0]        
        postprocess(nifti_dir, coreg_dir, seg_dir, output_dir, dcm_source_file, tumor_volume)
        # Move all the output files/folders to a subfolder named after the Accession Number
        ds = dcmread(dcm_source_file, stop_before_pixels=True)
        accession_number = ds.get("AccessionNumber", "output").strip()
        new_output_dir = os.path.join(output_dir, accession_number)
        if not os.path.exists(new_output_dir):
            os.makedirs(new_output_dir)
            p = Path(new_output_dir)
            p.chmod(p.stat().st_mode | stat.S_IROTH | stat.S_IXOTH | stat.S_IWOTH)
        for f in os.listdir(output_dir):
            if f != accession_number:
                os.rename(os.path.join(output_dir, f), os.path.join(new_output_dir, f))
    else:
        print("### Skipping postprocessing...")

    # set permissions for output files
    print("### Setting file permissions...")
    for root, dirs, files in os.walk(output_dir):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o777)
        for f in files:
            os.chmod(os.path.join(root, f), 0o777)

    end = time.time()

    print("### Done with processing")
    print("### Runtime:", end - start)


if __name__ == "__main__":
    run_pipeline("/data/")
