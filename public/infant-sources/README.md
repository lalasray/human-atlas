[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)][license]

# Morphological atlas of neonatal brain development
![Atlas images](figures/overview.png)

Spatio-temporal neonatal brain atlas constructed as part of the [Developing Human Connectome Project (dHCP)][dhcp].
The methodology used to built this temporally consistent atlas was first presented in [Schuh, 2017][Schuh2017-hdl] and [Schuh *et al.*, 2018][Schuh2018-doi].

*For a cortical surface atlas following a related but different approach [(Bozek et al., 2018)][Bozek2018-doi],
follow [this link][surface-atlas].*


## Content

Directory                 | Description
:-------------------------|:----------------------------------------------------------------------------------
[config](config/)         | Configuration files with [parameters](config/params.json) used to build the atlas and [ages](config/sessions.csv) of the neonates.
[figures](figures/)       | Images of figures displayed in this README file.
[global](global/)         | Affine transformations used to globally normalise the input brain images.
[mean](mean/)             | Contains the mean intensity images and hard segmentations for gestational age 36 to 44 weeks.
[structures](structures/) | Posterior probability maps of the [87 brain structures](config/structures.txt) for each atlas time point.
[tissues](tissues/)       | Posterior probability maps of the [9 tissue classes](config/tissues.txt) for each atlas time point.
[scale](scale/)           | Regressed anisotropic global scaling of each atlas time point.

The following image files are located underneath the age-specific directories (`ga_{36..44}`) of the `mean` folder:

Image file           | Description
:--------------------|:---------------------------------------------------------------------------
`mask.nii.gz`        | Average brain extraction mask.
`average_t1.nii.gz`  | Mean T1-weighted intensity image.
`average_t2.nii.gz`  | Mean T2-weighted intensity image.
`template_t1.nii.gz` | Mean T1-weighted intensity image after Laplacian sharpening.
`template_t2.nii.gz` | Mean T2-weighted intensity image after Laplacian sharpening.
`tissues.nii.gz`     | Hard tissue segmentation into [9 tissue classes](config/tissues.txt).
`structures.nii.gz`  | Structural segmentation into [87 brain structures](config/structures.txt).

It should be noted that all images are in a common global reference coordinate system. Therefore, the atlas images do not reflect global differences in average brain size between different atlas time points. The regressed anisotropic scaling factors for each atlas time point are provided. These can be applied to the images of the individual time points in order to create an image sequence which includes the global changes in brain size. How this can be done using the [MIRTK][mirtk], see [below](#software).

*Note: The posterior maps of tissue classes and brain structures may be downloaded as separate archives.*


## License

This brain atlas is distributed under the terms of the [Creative Commons Attribution 4.0 International][license] license.
<!-- See accompanying LICENSE.md file for details or follow the link given below. -->


## Citation

[Andreas Schuh][aschuh], [Antonios Makropoulos][amakropoulos], [Emma C. Robinson][erobinson], Lucilio Cordero-Grande, Emer Hughes, Jana Hutter, Anthony N. Price, Maria Murgasova, Rui Pedro A. G. Teixeira, Nora Tusor, Johannes Steinweg, Suresh Victor, Mary A. Rutherford, Joseph V. Hajnal, A. David Edwards, and [Daniel Rueckert][drueckert], **Unbiased construction of a temporally consistent morphological atlas of neonatal brain development**, *bioRxiv*, 2018. **doi:** [10.1101/251512][Schuh2018-doi]


    @article {Schuh2018,
      author = {Schuh, Andreas and Makropoulos, Antonios and Robinson, Emma C. and Cordero-Grande, Lucilio and Hughes, Emer and Hutter, Jana and Price, Anthony N and Murgasova, Maria and Teixeira, Rui Pedro A. G. and Tusor, Nora and Steinweg, Johannes K. and Victor, Suresh and Rutherford, Mary A. and Hajnal, Joseph V. and Edwards, A. David and Rueckert, Daniel},
      title = {Unbiased construction of a temporally consistent morphological atlas of neonatal brain development},
      journal = {bioRxiv},
      year = {2018},
      doi = {10.1101/251512},
      publisher = {Cold Spring Harbor Laboratory}
    }


## Materials

The used structural brain magnetic resonance images were collected at St. Thomas Hospital, London, UK, on a Philips 3T scanner using a dedicated 32 channel neonatal head coil as part of the [Developing Human Connectome Project (dHCP)][dhcp].

T2-weighted images were obtained in two stacks of 2D slices using a Turbo Spin Echo (TSE) sequence using TR = 12 s, TE = 156 ms, SENSE factor 2.11 (axial) and 2.58 (sagittal). T1-weighted images were obtained using an Inversion Recovery TSE sequence with TR = 4.8 s, TE = 8.7 ms, SENSE factor 2.26 (axial) and 2.66 (sagittal). Images were acquired with overlapping slices at a resolution of 0.8 x 0.8 x 1.6 mm<sup>3</sup>. During motion corrected reconstruction, the images are resampled to an isotropic voxel size of 0.5 mm. Babies were imaged without sedation during natural sleep. The used images showed no structural abnormalities. Details of the image selection from in total 495 processed images are given in [Schuh *et al.*, 2018][Schuh2018-doi].

The histograms below show the distribution of gestational age at birth (steps) and post-menstrual age at scan (bars) of the dataset consisting of 275 T1-weighted and T2-weighted brain images used to construct this spatio-temporal brain atlas.

![Age distribution](figures/distribution.png)


## Methods

All reconstructed volumes were preprocessed using a pipeline designed for neonatal brain images, including an initial rough brain extraction and bias field correction. The images were segmented into 87 regions of interest (ROIs) and 9 tissue classes (background, CSF, cGM, dGM, WM, ventricles, cerebellum, brainstem, hippocampi and amygdalae) using an extension of the [Developing Brain Region Annotation With Expectation-Maximization (Draw-EM)][drawem] algorithm. A detailed description of this pipeline is given in [Makropoulos *et al.*, 2018][Makropoulos2018-doi], and the [source code][Makropoulos2018-src] is available on GitHub.


![Atlas construction](figures/construction.png)

The spatio-temporal neonatal brain atlas construction is summarised in [Schuh *et al.*, 2018][Schuh2018-doi].
Further details, including an evaluation of the employed diffeomorphic registration method, can be found in [Schuh, 2017][Schuh2017-hdl].


## Software

A software implementation in Python and C++ of the methodology used to built this spatio-temporal atlas is part of the [Medical Image Registration ToolKit (MIRTK)][mirtk], an open source image processing toolkit [available on GitHub][mirtk-web]. The parameters used for this software tool can be found in the [config/params.json](config/params.json) file. Specifically, we used [MIRTK v2.0][mirtk-v2.0].

Given an installation of MIRTK, the atlas construction can be executed using the command:


    mirtk construct-atlas config/params.json

*Note: This requires additional input image files which are not distributed as part of this atlas. While not publicly available as of July 2018, the used reconstructed brain images and corresponding segmentations are expected to be released by the dHCP team at https://data.developingconnectome.org/.*

An image sequence which includes the regressed average changes in brain size can be created, for example from the T2-weighted template images, using the following MIRTK commands executed on a Unix system in a [Bash shell](https://www.gnu.org/software/bash/manual/html_node/What-is-Bash_003f.html), where the current working directory is assumed to be set to the top-level directory of this atlas:

    # Apply global scalings
    mkdir -p temp
    for t in {36..44}; do
        mirtk transform-image mean/ga_$t/template_t2.nii.gz temp/template_t2_$t.nii.gz -dofin scale/ga_$t.dof -invert
    done

    # Combine 3D volumes into 3D+t image sequence
    mirtk combine-images -images temp/template_t2_{36..44}.nii.gz -output seq.nii.gz

    # Display image sequence using MIRTK viewer
    mirtk view seq.nii.gz

    # Delete output files (optional)
    rm -f temp/template_t2_{36..44}.nii.gz
    rmdir temp 2> /dev/null


## Acknowledgements

The work resulting in this brain atlas was done in the [Biomedical Image Analysis (BioMedIA)][biomedia] group at [Imperial College London][icl] as part of the [dHCP][dhcp], which received funding from the European Research Council under the European Union's Seventh Framework Programme (FP/2007-2013) [grant no. 319456]. We are grateful to the families who generously supported this trial. The work was supported by the NIHR Biomedical Research Centers at Guy's and St Thomas' NHS Trust.


## References


*Data acquisition:*

E. J. Hughes, T. Winchman, F. Padormo, R. Teixeira, J. Wurie, M. Sharma, M. Fox, J. Hutter, L. Cordero-Grande, A. N. Price, J. Allsop, J. Bueno-Conde, N. Tusor, T. Arichi, A. D. Edwards, M. A. Rutherford, S. J. Counsell, and J. V. Hajnal, **A dedicated neonatal brain imaging system**, *Magnetic Resonance in Medicine*, vol. 78 (2), pp. 794-804, 2017.
[[abstract]][Hughes2016-doi] [[pdf]][Hughes2016-pdf]


*Motion corrected reconstruction:*

L. Cordero-Grande, E. J. Hughes, J. Hutter, A. N. Price, and J. V. Hajnal, **Three-dimensional motion corrected sensitivity encoding reconstruction for multi-shot multi-slice MRI: Application to neonatal brain imaging**, *Magnetic Resonance in Medicine*, vol. 79 (3), pp. 1365-76, 2018.
[[abstract]][CorderoGrande2018-doi] [[pdf]][CorderoGrande2018-pdf]


*Brain segmentation:*

A. Makropoulos, E. C. Robinson, A. Schuh, R. Wright, S. Fitzgibbon, J. Bozek, S. J. Counsell, J. Steinweg, K. Vecchiato, J. Passerat-Palmbach, G. Lenz, F. Mortari, T. Tenev, E. P. Duff, M. Bastiani, L. Cordero-Grande, E. Hughes, N. Tusor, J.-D. Tournier, J. Hutter, A.N. Price, R. P. A. G. Teixeira, M. Murgasova, S. Victor, C. Kelly, M. A. Rutherford, S. M. Smith, A. D. Edwards, J. V. Hajnal, M. Jenkinson, D. Rueckert, **The developing human connectome project: A minimal processing pipeline for neonatal cortical surface reconstruction**, *NeuroImage*, vol. 173, pp. 88-112, 2018.
[[abstract]][Makropoulos2018-doi] [[pdf]][Makropoulos2018-pdf] [[code]][Makropoulos2018-src]


*Image registration and atlas construction:*

A. Schuh, **Computational models of the morphology of the developing neonatal human brain**, *PhD thesis*, 2017.
[[abstract]][Schuh2017-hdl] [[pdf]][Schuh2017-pdf]

A. Schuh, A. Makropoulos, E. C. Robinson, L. Cordero-Grande, E. Hughes, J. Hutter, A. N. Price, M. Murgasova, R. P. A. G. Teixeira, N. Tusor, J. Steinweg, S. Victor, M. A. Rutherford, J. V. Hajnal, A. D. Edwards, and D. Rueckert, **Unbiased construction of a temporally consistent morphological atlas of neonatal brain development**, *bioRxiv*, preprint, 2018.
[[abstract]][Schuh2018-doi] [[pdf]][Schuh2018-pdf] [[code]][Schuh2018-src]


<!-- Links -->
[license]: https://creativecommons.org/licenses/by/4.0/

[aschuh]: http://andreasschuh.com/
[amakropoulos]: http://antoniosmakropoulos.com/
[erobinson]: https://emmarobinson01.com/
[drueckert]: https://wp.doc.ic.ac.uk/dr/

[biomedia]: https://biomedic.doc.ic.ac.uk
[icl]: http://www.imperial.ac.uk/computing
[dhcp]: http://www.developingconnectome.org/project/
[surface-atlas]: https://brain-development.org/brain-atlases/cortical-surface-atlas/
[drawem]: https://biomedia.doc.ic.ac.uk/software/draw-em/
[mirtk]: https://biomedia.doc.ic.ac.uk/software/mirtk/
[mirtk-web]: https://mirtk.github.io/
[mirtk-v2.0]: https://github.com/BioMedIA/MIRTK/releases/tag/v2.0.0

[Bozek2018-doi]: https://doi.org/10.1016/j.neuroimage.2018.06.018

[Hughes2016-doi]: https://doi.org/10.1002/mrm.26462
[Hughes2016-pdf]: https://onlinelibrary.wiley.com/doi/epdf/10.1002/mrm.26462

[CorderoGrande2018-doi]: https://doi.org/10.1002/mrm.26796
[CorderoGrande2018-pdf]: https://onlinelibrary.wiley.com/doi/epdf/10.1002/mrm.26796

[Makropoulos2018-doi]: https://doi.org/10.1016/j.neuroimage.2018.01.054
[Makropoulos2018-pdf]: https://www.biorxiv.org/content/early/2018/01/07/125526.full.pdf
[Makropoulos2018-src]: https://github.com/BioMedIA/dhcp-structural-pipeline

[Schuh2017-hdl]: http://hdl.handle.net/10044/1/58880
[Schuh2017-pdf]: https://spiral.imperial.ac.uk/bitstream/10044/1/58880/1/Schuh-A-2018-PhD-Thesis.pdf

[Schuh2018-doi]: https://doi.org/10.1101/251512
[Schuh2018-pdf]: https://www.biorxiv.org/content/early/2018/01/28/251512.full.pdf
[Schuh2018-src]: https://github.com/BioMedIA/MIRTK/releases/tag/v2.0.0
