# RSVQA Code
This readme presents the step required to generate the databases and reproduce the results presented in [1]. Please cite this article if you use this code.

## Automatic generation of the DB:
The automatic generation of the databases is handled by the scripts in the AutomaticDB folder, and can be launched with the process.py script.

It works by intersecting geotagged images with elements from OSM.
It has been checked to work on USGS' ortophotos or S2 tiles.
You should set the access to the zip files at line 233 of process.py.
The postgresql DB should be populated with OSM data covering the extent of the images. This OSM data can for instance be obtained here: http://download.geofabrik.de/

In AutomaticDB/vqa_database.ini, you should configure the access to a postgresql database, as well as the access to the scentinel hub portal that can be obtained here: https://scihub.copernicus.eu/ (optional, you can also directly download the tiles)
These fields are marked with "TO_REPLACE"

## Training the models
The files regarding the model are put in the VQA_model folder.
The architecture is defined in models/model.py, and you can use train.py to launch a training.

You will need, in addition to the packages found in requirements.txt, to install skipthoughts:

    git clone https://github.com/Cadene/skip-thoughts.torch.git
    cd skip-thoughts.torch/pytorch
    python setup.py install

Available here:
https://github.com/Cadene/skip-thoughts.torch/tree/master/pytorch

# Thanks
The authors would like to thank Rafael Félix for his remarks and the requirements.txt file.

# References
[1] Lobry, Sylvain, et al. "RSVQA: Visual question answering for remote sensing data." IEEE Transactions on Geoscience and Remote Sensing 58.12 (2020): 8555-8566.