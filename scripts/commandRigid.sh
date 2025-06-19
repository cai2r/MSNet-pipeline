#! /bin/sh
#adapted from https://github.com/ntustison/PartialSlabEpiT1ImageRegistration/blob/master/commandRigid.sh

baseDirectory=/data

fixedImage=${baseDirectory}/4-skull-strip/brain_t1ce.nii.gz
movingImage=${baseDirectory}/2-nifti/brain_perfusion.nii.gz

# Register T1 to EPI slab with mask
outputPrefix=perfusion

antsRegistration --verbose 1 \
                 --dimensionality 3 \
                 --float 0 \
                 --interpolation Linear \
                 --use-histogram-matching 0 \
                 --winsorize-image-intensities [0.005,0.995] \
                 --output [${outputPrefix},${outputPrefix}Warped.nii.gz,${outputPrefix}InverseWarped.nii.gz] \
                 --initial-moving-transform [${fixedImage},${movingImage},1] \
                 --transform translation[0.1] \
                   --metric MI[${fixedImage},${movingImage},1,32,Random,0.25] \
                   --convergence [50,1e-6,10] \
                   --shrink-factors 1 \
                   --smoothing-sigmas 0vox \
                 --transform Rigid[0.1] \
                   --metric MI[${fixedImage},${movingImage},1,32,Random,0.25] \
                   --convergence [500x250x50,1e-6,10] \
                   --shrink-factors 2x2x1 \
                   --smoothing-sigmas 2x1x0vox 