from enum import Enum
from enum import IntEnum


class BinaryMasksMSNet(IntEnum):
    TUMOR_CORE = 1
    WHOLE_TUMOR = 2
    ENHANCING_TUMOR = 4


class BinaryMasksNnuNet(IntEnum):
    WHOLE_TUMOR = 2
    TUMOR_CORE = 3
    ENHANCING_TUMOR = 1


class NiftiExtensions(Enum):
    COMPRESSED_NIFTI = ".nii.gz"
    NIFTI = ".nii"

    def get_extensions():
        return [extension.value for extension in NiftiExtensions]


class DicomExtensions(Enum):
    DICOM = ".dcm"


# TODO: parse this as JSON probably
modalities = {
    "t1ce": [
        "SAG_MPR",
        "AX_3D_MPR",
        "AX_MPR_FBH",
        "SAG_3D_MPR",
        "SAG_CS_MPRAGE",
        "T1_3D_POST",
        "T1CE",
    ],
    "t1": ["AX_T1_PRE", "AX_T1", "T1"],
    "t2": [
        "AX_T2",
        "SAG_T2_SPACE",
        "3D_T2_SPACE",
        "BRAIN_MAPPING_T2_SPACE",
        "SAG_3D_T2",
        "Head_AX_PD_T2",
        "T2",
    ],
    "flair": [
        "SAG_3D_FLAIR",
        "CS_3D_FLAIR_SPACE",
        "BRAIN_MAPPING_FLAIR_SPACE",
        "SAG_FLAIR_SPACE",
        "3D_FLAIR_SPACE",
        "SAG_SPACE_FLAIR",
        "SAG_3D_FLAIR_SPACE",
        "SPACE_FLAIR",
        "SAG_SPACE_FLAIR_256_FOV",
        "SPACE_3D_FLAIR",
        "SAG_FLAIR_SPACE_(if_no_SPACE_then_SAG_FLAIR)",
        "AX_FLAIR",
        "FLAIR",
        "FL",
    ],
    "diffusion": [
        "Diffusion_1e-3mm_s",
        "AX_DIFFUSION_ADC",
        "AX_DIFFUSION-P_ADC",
        "AX_DIFFUSION_SMS_ADC",
        "BRAIN_MAPPING_meso_ADC",
        "BRAIN_MAPPING_2mmiso_meso_RMR_ADC",
    ],
    "perfusion": ["MR_Perfusion"],
}
