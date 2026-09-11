# Newborn mesh

## Description:
This dataset contains a labelled mesh of the thorax of a newborm premature human baby with the sectionning of different region of the body.
The mesh is composed of 229363 nodes that are grouped into 1356069 tetrahedron elements.

## Original data
The original DICOM (Digital Imaging and communications in medicine) images belong to the Cork University Hospital (CUH) data base. 
The hospital contacted the parents who approved the academic use of the anonymised CT scan of their child, under the ethical approval 
ECM 4 (gg) 07/03/18 from the Clinical Research Ethics Committee of the Cork Teaching Hospitals.
The thoracic CT scan consist of a stack of 367 cross sectional slices, 0.625 mm thick. The area of each image is 512 x 512 pixels with a pixel
size of 0.3555 mm. The neonate was born at 36 weeks gestational age with 3.58 kg weight. 

## Sectioning process
The segmentation of nine main organs (skin, fat, muscle, bone, cartilage, heart, artery, trachea and lung) was done using NIRFASTSlicer2.0.
Each DICOM image exhibits the different organs in an especific Housenfield Unit (HU, quantitave scale of radiodensity); dense organs like bone 
have whitish color, in contrast with less dense organs which appereance is dark.  A distinctive colour was assigned to each organ by direct 
drawing over the CT images one by one. The HU were used to define the boundaries between organs. 
The organs were considered homogeneous, therefore fine structures present in the human body were ignored.

For our study, we subdivided the lungs into 3 different segments (inner, middle and external). 
On completion of segmentation, the thoracic CT was subdivided in the 11 regions. 

## Regions
The mesh has been divided in 11 different regions number from 1 to 11 in the following way:
- 1 -> lung (external segment)
- 2 -> bone
- 3 -> cartilage
- 4 -> heart
- 5 -> muscle
- 6 -> artery
- 7 -> fat
- 8 -> skin
- 9 -> trachea
- 10 -> lung (middle segment)
- 11 -> lung (inner segment)

## Data format
The mesh data is written in 3 different file format:
 - mesh.mat: MATLAB .mat format that contains 5 variables:
	- dimension: Number of dimension in the mesh
	- nodes: Matrix of size 229363 x 3 containing the (x,y,z) coordinates of each node in the mesh in milimetres (mm)
	- elements: Matrix of size 1356096 x 4 containing the indices of the nodes corresponding to each element (tetrahedron) of the mesh
	- region: Vector size 229363 x 1 indicating to which region the nodes belongs.
	- bndvtx: Vector of size 229363 x 1 indicating whether the node is on the boundary of the mesh.
 - mesh.vtk: Mesh in the vtk Datafile Version 2.0 format. The only data field in the VTK file corresponds to the region variable in the .mat file.
 - mesh_csv.zip: Mesh in a .csv format. The zip file contains 4 csv files containing the nodes list, the elements list, the region list and the bndvtx list.

## Licence
The mesh is published under the creative common CC-BY licence. You are free to use this data as you wish, but please cite this dataset using its DOI for example.

## Digital Object Identifier:
DOI: 10.5281/zenodo.4916863

## Authors
Mesh sectionning: Andrea Pacheco
Data formating: Baptiste Jayet

## Funding
The research leading to these results was funded by Science Foundation Ireland project no. SFI/15/RP/2828 