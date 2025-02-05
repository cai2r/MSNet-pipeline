"""
This module contains all the required post-processing data transformations
starting from NIfTI files output by an ML model and ending with a DICOM file.
"""
from enum import IntEnum
from pathlib import Path
from typing import Generator
import os
import stat
from pathlib import Path

import cv2
import numpy as np
import pydicom
from PIL import Image
import nibabel as nib
from scipy.ndimage import zoom
import json

from src.common.enums import BinaryMasksMSNet

def arr2dicom(
    arr: np.ndarray,
    dicom_file: pydicom.dataset.FileDataset,
    series_uid: pydicom.uid.UID,
    series_description: str,
    slice_idx: int,
) -> pydicom.dataset.FileDataset:
    """Converts a 2D numpy array into a DICOM file.

    Args:
        arr: 2D numpy array to convert into a DICOM file.
        dicom_file: DICOM file to use as a template for the new DICOM files. Metadata will be copied from this file.
        series_uid: Series UID of the new DICOM file.
        series_description: Series description of the new DICOM file.
        slice_idx: Slice index to use for the patient position of the new DICOM file.

    Returns:
        DICOM file with the same metadata as the input DICOM file and the pixel data from the input numpy array.

    """
    ds = dicom_file.copy()

    ds.SeriesInstanceUID = series_uid
    ds.SeriesDescription = series_description.upper()
    ds.SOPInstanceUID = pydicom.uid.generate_uid()

    # adjust the shape of the DICOM image to match the masked slice
    ds.Rows = arr.shape[0]
    ds.Columns = arr.shape[1]
    # adjust the expected range of pixels in the image data, we have normalized to 0-255
    # this is information DICOM viewers use to adjust brightness/constrast for display
    ds.WindowCenter = 128
    ds.WindowWidth = 256
    ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
    # tag which slice in the volume we're dealing with
    ds.ImagePositionPatient = [0, 0, slice_idx]
    ds.InstanceNumber = slice_idx + 1

    # specify transfer syntax to assign pixel data
    ds.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
    #ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
     
    # assign values for a color DICOM instead of a grayscale
    ds.PhotometricInterpretation = "RGB"
    ds.SamplesPerPixel = 3
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    #ds.PixelRepresentation = 0
    #ds.PlanarConfiguration = 0
    #--update
    
     #--update
    ds.is_little_endian=True
    ds.is_implicit_VR=False
    #ds.is_original_encoding=False

    ds.add_new(0x00280006, 'US', 0)
    ds.fix_meta_info() 
    

    # copy the array containing the masked slice image to pixel data
    ds.PixelData = arr.tobytes()
    ds.ImageType = "DERIVED\\SECONDARY"
    
    return ds


def pad_nifti_data(nifti_data):
    # pad data to 256x256x256
    nifti_data = np.pad(
        nifti_data,
        (
            (
                int((256 - nifti_data.shape[0]) / 2),
                int((256 - nifti_data.shape[0]) / 2),
            ),
            (
                int((256 - nifti_data.shape[1]) / 2),
                int((256 - nifti_data.shape[1]) / 2),
            ),
            (
                int((256 - nifti_data.shape[2]) / 2),
                int((256 - nifti_data.shape[2]) / 2),
            ),
        ),
        "constant",
        constant_values=0,
    )

    return nifti_data


def nifti2dicom(
    nifti_path,
    dicom_path,
    output_dir,
    output_prefix,
) -> None:
    """Converts a NIfTI file into a DICOM file.

    Args:
        nifti_path: Path to the NIfTI file.
        dicom_path: Path of the DICOM file to use as a template for the new DICOM files. Metadata will be copied from
            this file.
        output_dir: Directory where the final DICOM file will be saved.
        output_prefix: Prefix for the output DICOM files.
    """
    # read in NIfTI file data
    nifti_data = nib.load(nifti_path).get_fdata()
    if len(nifti_data.shape) == 4:
        nifti_data = nifti_data[:, :, :, 0]

    # grab info from dicom file
    dicom_file = pydicom.dcmread(dicom_path)

    print(output_prefix)

    # diffusion and perfusion are not coregistered, they should be scaled
    # Note: Disabled to avoid flipping of diffusion image    
    # if ("diffusion" in output_prefix):# or ("perfusion" in output_prefix):
    #     zoom_factor = nib.load(nifti_path).header.get_zooms()
    #     nifti_data = zoom(nifti_data, zoom_factor)
    #     nifti_data = np.flip(nifti_data, axis=(0))
        
    # reorient arrays to save DICOM slices in AXIAL orientation
    nifti_data = np.rot90(nifti_data, axes=(0, 2))
    nifti_data = np.flip(nifti_data, axis=(1, 2))

    nifti_data = pad_nifti_data(nifti_data)

    arr_min = nifti_data.min()
    arr_max = nifti_data.max()

    # iterate over slices and save them as DICOM files
    series_uid = pydicom.uid.generate_uid()
    for i in range(nifti_data.shape[0]):
        slice = nifti_data[i, :, :]
        slice = normalize_background_arr(slice, arr_min, arr_max)
        slice = Image.fromarray(slice).convert("RGB")
        slice = np.array(slice, dtype=np.uint8)
        output_dicom_file = arr2dicom(slice, dicom_file, series_uid, output_prefix, i)
        output_filename = (Path(output_dir) / f"{output_prefix}_{i + 1}").with_suffix(
            ".dcm"
        )
        output_dicom_file.save_as(output_filename)
        #p = Path(output_filename)
        #p.chmod(p.stat().st_mode | stat.S_IROTH | stat.S_IXOTH | stat.S_IWOTH)


def masked2dicom(
    mask_path,
    background_file,
    dicom_path,
    output_dir,
    mask_values,
    modality,
    tumor_stats,
) -> dict:
    """Converts a NIfTI file with the tumor segmentation mask overlapped into multiple DICOM files where each file
    corresponds to a slice.

    Args:
        mask_path: Path to the segmentation mask NIfTI file.
        background_file: Object with the background NIfTI file. We load this object from memory because the original
            file from where this object was created might not exist at this point.
        dicom_path: Path of the DICOM file to use as a template for the new DICOM files. Metadata will be copied from
            this file.
        output_dir: Directory where the final DICOM files will be saved.
        mask_values: Enum mapping tumor subregion segmentations to their label number in composite mask
        output_prefix: Prefix for the output DICOM files.
        tumor_volume: dict with keys [total, enhancing, non_enhancing, edema] and corresponding float values.

    Returns:
        DICOM file with the modality overlapped by the tumor segmentation mask.

    """
    #TODO: need to add function to calculate mean ADC if modality = diffusion 
    mask_array = nib.load(mask_path).get_fdata()
    background_array = nib.load(background_file).get_fdata()
    dicom_file = pydicom.dcmread(dicom_path)
    output_prefix = "masked_"+ modality

    if modality=='diffusion' or modality=='perfusion':
        tumor_stats["enhancing portion"]= round(np.mean(background_array[(mask_array == mask_values.ENHANCING_TUMOR.value) & (background_array > 0)]),3)
        tumor_stats["total vasogenic edema volume"]= round(np.mean(background_array[(mask_array == mask_values.WHOLE_TUMOR.value) & (background_array > 0)]),3)
        tumor_stats["non enhancing portion"]= round(np.mean(background_array[(mask_array == mask_values.TUMOR_CORE.value) & (background_array > 0)]),3)
        if modality=='diffusion':
            tumor_stats["unit"]= "1e-3 mm2/s"
        if modality=='perfusion':
            tumor_stats["unit"]= "ml/100ml"
    # reorient arrays to save DICOM slices in AXIAL orientation
    mask_array = np.rot90(mask_array, axes=(0, 2))
    mask_array = np.flip(mask_array, axis=(1, 2))
    background_array = np.rot90(background_array, axes=(0, 2))
    background_array = np.flip(background_array, axis=(1, 2))

    # pad slice and mask arrays to 256x256x256
    mask_array = pad_nifti_data(mask_array)
    background_array = pad_nifti_data(background_array)

    # Create the template of the overlay
    [stats_dict, overlay] = generate_overlay_arr(
        tumor_stats, (background_array.shape[1], background_array.shape[2]), modality
    )

    # Generator of slices with the mask and template overlapping the background
    masked_slices = merge3D_mask_arr(mask_array, background_array, mask_values, overlay)

    # iterate over slices and save them as DICOM files
    series_uid = pydicom.uid.generate_uid()
    for i, slice in enumerate(masked_slices):
        output_dicom_file = arr2dicom(slice, dicom_file, series_uid, output_prefix, i)
        output_filename = (Path(output_dir) / f"{output_prefix}_{i + 1}").with_suffix(
            ".dcm"
        )
        output_dicom_file.save_as(output_filename)
        #p = Path(output_filename)
        #p.chmod(p.stat().st_mode | stat.S_IROTH | stat.S_IXOTH | stat.S_IWOTH)
    
    return stats_dict

def merge3D_mask_arr(
    mask_arr: np.ndarray,
    background_arr: np.ndarray,
    mask_values: IntEnum,
    overlay: np.ndarray,
) -> Generator:
    """Merges the segmentation mask array with an array corresponding to the background.

    Args:
        mask_arr: Array corresponding to the segmentation mask.
        background_arr: Array corresponding to the background.
        mask_values: Enum mapping tumor subregion segmentations to their label number in composite mask
        overlay: Image array to use as a DICOM overlay plane

    Yields:
        Array of merged slices.

    """
    len_mask = mask_arr.shape[0]
    len_background = background_arr.shape[0]
    assert len_mask == len_background, (
        f"Number of slices in the segmentation mask ({len_mask}) has to be the same as the number of slices "
        f"in the background file ({len_background})"
    )

    for i in range(mask_arr.shape[0]):
        yield merge2D_mask_arr(
            mask_arr[i, :, :], background_arr[i, :, :], mask_values, overlay
        )


def merge2D_mask_arr(
    mask: np.ndarray,
    background_arr: np.ndarray,
    mask_values: IntEnum,
    overlay: np.ndarray,
) -> np.ndarray:
    """Merges a slice of the segmentation mask array with an array corresponding to the background at the same slice.

    Args:
        mask: Array corresponding to a slice of the segmentation mask.
        background_arr: Array corresponding to a slice of the background.
        mask_values: Enum mapping tumor subregion segmentations to their label number in composite mask
        overlay: Image array to use as a DICOM overlay plane

    Returns:
        Array corresponding to the merged mask of a slice.

    """
    # Mask has 3 possible values
    # TODO: move this to its own function and generalize labels
    binary_mask_1 = np.where(mask == mask_values.ENHANCING_TUMOR.value, 255, 0).astype(
        np.ubyte
    )
    binary_mask_2 = np.where(mask == mask_values.WHOLE_TUMOR.value, 255, 0).astype(
        np.ubyte
    )
    binary_mask_3 = np.where(mask == mask_values.TUMOR_CORE.value, 255, 0).astype(
        np.ubyte
    )
    mask_rgb = np.dstack((binary_mask_1, binary_mask_2, binary_mask_3))
    mask_rgb_pil = Image.fromarray(mask_rgb)

    # Normalize background array
    background_arr = normalize_background_arr(background_arr, background_arr.min(), background_arr.max())
    background_arr_pil = Image.fromarray(background_arr).convert("RGB")

    # Merge mask and background
    merged_pil = Image.blend(mask_rgb_pil, background_arr_pil, 0.7)
    merged_pil = np.array(merged_pil, dtype=np.uint8)

    # Overlay research warning and volumetric info
    # Create a mask of the second image
    gray = cv2.cvtColor(overlay, cv2.COLOR_BGR2GRAY)
    ret, mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
    mask_inv = cv2.bitwise_not(mask)
    # Apply the mask to the second image
    overlay_fg = cv2.bitwise_and(overlay, overlay, mask=mask)
    merged_pil_bg = cv2.bitwise_and(merged_pil, merged_pil, mask=mask_inv)
    # combine the overlay and merged slice
    merged_with_overlay = cv2.add(merged_pil_bg, overlay_fg)

    # It is necessary to use uint8 to show RGB images on DICOM
    return merged_with_overlay


def normalize_background_arr(background_arr: np.ndarray, arr_min: int, arr_max: int) -> np.ndarray:
    """Normalizes the background array between 0 and 255.

    Args:
        background_arr: Array corresponding to a slice of the background.

    Returns:
        Array corresponding to the normalized background.

    """
    # Normalize only positive values to avoid division by zero
    # The if statement is here to avoid a warning when all values are zero
    if np.any(background_arr):
        background_arr = np.where(
            background_arr > 0,
            (
                255
                * (1.0 / arr_max * (background_arr - arr_min))
            ),
            background_arr,
        )

    return background_arr


def generate_overlay_arr(tumor_stats: dict, slice_shape: tuple, modality):# -> tuple[dict, np.ndarray]:
    """Bitmaps the volumetric information into a overlay image.

    Args:
        tumor_volume: dict with keys [total, enhancing, non_enhancing, edema] and corresponding float values.
        slice_shape: tuple of the standard slice shape

    Returns:
        Image array to use as a DICOM overlay plane
    """
    # set blank array
    bitmap = np.zeros(shape=(slice_shape[0], slice_shape[1], 3), dtype=np.uint8)

    # set text visual specs
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.3
    color_blue = (255, 0, 0)
    color_green = (0, 255, 0)
    color_red = (0, 0, 255)
    color_white = (255, 255, 255)
    thickness = 1
    line_type = cv2.LINE_4

    # text to display
    research_warning = ["FOR RESEARCH ONLY;", "REFER TO OFFICIAL REPORT FOR DETAILS"]
    legend_headers = "Legend"
    stats_d={}
    if modality =='diffusion' or modality =='perfusion':
        edema_text = (
            "Edema      "
            + str(tumor_stats["total vasogenic edema volume"])
            + " "
            +tumor_stats["unit"]
        )
        enhancing_text = (
            "Enhancing  "
            + str(tumor_stats["enhancing portion"])
            + " "
            + tumor_stats["unit"]
        )
        non_enhancing_text = [
            "Non-       "
            + str(tumor_stats["non enhancing portion"])
            + " "
            + tumor_stats["unit"],
            "Enhancing",
        ]
    else:
        tumor_volume = tumor_stats
        edema_text = (
            "Edema      "
            + str(tumor_volume["total vasogenic edema volume"])
            + "+/-6.3 "
            + tumor_volume["unit"]
        )
        enhancing_text = (
            "Enhancing  "
            + str(tumor_volume["enhancing portion"])
            + "+/-13.2 "
            + tumor_volume["unit"]
        )
        non_enhancing_text = [
            "Non-       "
            + str(tumor_volume["non enhancing portion"])
            + "+/-2.7 "
            + tumor_volume["unit"],
            "Enhancing",
        ]
    stats_d[f"{modality}_edema"] = edema_text
    stats_d[f"{modality}_enhancing"] = enhancing_text
    stats_d[f"{modality}_non_enhancing"] = " ".join(non_enhancing_text)
    
    # add fixed text (research disclaimer, legend headers) to bitmap
    bitmap = cv2.putText(
        bitmap,
        text=research_warning[0],
        org=(int(slice_shape[1] // 20), int(slice_shape[0] // 10)),
        fontFace=font,
        fontScale=font_scale,
        color=color_white,
        thickness=thickness,
        lineType=line_type,
    )
    bitmap = cv2.putText(
        bitmap,
        text=research_warning[1],
        org=(int(slice_shape[1] // 20), int(slice_shape[0] * 1.4 // 10)),
        fontFace=font,
        fontScale=font_scale,
        color=color_white,
        thickness=thickness,
        lineType=line_type,
    )

    # add in legend template
    bitmap = cv2.putText(
        bitmap,
        text=legend_headers,
        org=(int(slice_shape[1] // 30), int(slice_shape[0] * 8.25 // 10)),
        fontFace=font,
        fontScale=font_scale,
        color=color_white,
        thickness=thickness,
        lineType=line_type,
    )
    bitmap = cv2.rectangle(
        bitmap,
        (int(slice_shape[1] // 30), int(slice_shape[0] * 8.5 // 10)),
        (int(slice_shape[1] * 3 // 30), int(slice_shape[0] * 8.75 // 10)),
        color_green,
        -1,
    )  # green rectangle
    bitmap = cv2.rectangle(
        bitmap,
        (int(slice_shape[1] // 30), int(slice_shape[0] * 8.9 // 10)),
        (int(slice_shape[1] * 3 // 30), int(slice_shape[0] * 9.15 // 10)),
        color_red,
        -1,
    )  # red rectangle
    bitmap = cv2.rectangle(
        bitmap,
        (int(slice_shape[1] // 30), int(slice_shape[0] * 9.3 // 10)),
        (int(slice_shape[1] * 3 // 30), int(slice_shape[0] * 9.55 // 10)),
        color_blue,
        -1,
    )  # blue rectangle

    # add volume numbers to bitmap
    bitmap = cv2.putText(
        bitmap,
        text=edema_text,
        org=(int(slice_shape[1] * 3.5 // 30), int(slice_shape[0] * 8.75 // 10)),
        fontFace=font,
        fontScale=font_scale,
        color=color_white,
        thickness=thickness,
        lineType=line_type,
    )
    bitmap = cv2.putText(
        bitmap,
        text=enhancing_text,
        org=(int(slice_shape[1] * 3.5 // 30), int(slice_shape[0] * 9.15 // 10)),
        fontFace=font,
        fontScale=font_scale,
        color=color_white,
        thickness=thickness,
        lineType=line_type,
    )
    bitmap = cv2.putText(
        bitmap,
        text=non_enhancing_text[0],
        org=(int(slice_shape[1] * 3.5 // 30), int(slice_shape[0] * 9.55 // 10)),
        fontFace=font,
        fontScale=font_scale,
        color=color_white,
        thickness=thickness,
        lineType=line_type,
    )
    bitmap = cv2.putText(
        bitmap,
        text=non_enhancing_text[1],
        org=(int(slice_shape[1] * 3.5 // 30), int(slice_shape[0] * 9.95 // 10)),
        fontFace=font,
        fontScale=font_scale,
        color=color_white,
        thickness=thickness,
        lineType=line_type,
    )

    return stats_d, bitmap


def postprocess(
    nifti_dir,
    coreg_dir,
    mask_dir,
    output_dir,
    dicom_source_file,
    tumor_volume: dict,
) -> None:
    """Runs the postprocessing step given a directory with a single NIfTI file.
    """

    mask_path = list(Path(mask_dir).glob("*_whole.nii.gz"))[0]
    print("starting nifti to dicom")
    nifti2dicom(
        mask_path,
        dicom_source_file,
        output_dir,
        "mask",
    )

    # convert perfusion to DICOM
    nifti_file = os.path.join(nifti_dir, 'brain_perfusion.nii.gz')
    # sometimes perfusion was not run, so check if file exists
    if os.path.exists(nifti_file):
        nifti2dicom(
        nifti_file,
        dicom_source_file,
        output_dir,
        "perfusion",
        )

    # convert diffusion to DICOM
    nifti_file = os.path.join(nifti_dir, 'brain_diffusion.nii.gz')
    # sometimes diffusion was not run, so check if file exists
    if os.path.exists(nifti_file):
        nifti2dicom(
        nifti_file,
        dicom_source_file,
        output_dir,
        "diffusion",
        )

    # get list of coregistered files
    nifti_files = os.listdir(coreg_dir)

    # get list of modalities
    modalities = []
    for file in nifti_files:
        modality = file.split('_')[1]
        modality = modality.split('.')[0]
        if modality not in modalities:
            modalities.append(modality)

    # convert each modality to DICOM
    for modality in modalities:
        nifti_file = os.path.join(coreg_dir, f'brain_{modality}.nii.gz')
        nifti2dicom(
            nifti_file,
            dicom_source_file,
            output_dir,
            modality,
        )

    # add masks to t1ce and flair
    all_results={}
    mask_values = BinaryMasksMSNet
    for modality in ['t1ce', 'flair','diffusion', 'perfusion']:
        nifti_file = os.path.join(coreg_dir, f'brain_{modality}.nii.gz')
        modality_results = masked2dicom(
            mask_path,
            nifti_file,
            dicom_source_file,
            output_dir,
            mask_values,
            modality,
            tumor_volume,
        )
        all_results.update(modality_results)

    # After the loop, write the cumulative dictionary to a JSON file
    
    output_file_path = os.path.join(output_dir, 'result.json')
    with open(output_file_path, 'w') as json_file:
        json.dump(all_results, json_file, indent=4)

    print(f"Results have been written to {output_file_path}")
