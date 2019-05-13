# mae-tao-omr
an OMR-based tool that automates data extraction from scanned medical records


Dependencies
============
- Python 3
- Python Imaging Library (PIL) (``python3-pil``, distributed as part of ``python3-Pillow``)
- Python lxml (``python3-lxml``)
- NumPy (``python3-numpy``)
- SciPy (``python3-scipy``)
- scikit-image (``python3-skimage``)
- opencv (``opencv-python``)
- pathlib (``pathlib``)
- flask (``flask``)

All of these can be installed used `pip` or `conda`. If you're trying to install `opencv` using `conda`, you may need to run `conda install -c menpo opencv`.


Getting Started
===============
To get a feel for how the scripts works, run the following line:

```
./bin/digitize ./example/template.jpg ./example/checkbox_locations.svg ./example/phone_pics/input/sample_pic.jpg
```


| Parameter                           | Description   |
| -------------                       |:--------------|
| `digitize`                          | an orchestration script that will call `align` and `simpleomr` in succession |
| `template.jpg`                      | a clean scan of a blank, unfilled record |
| `checkbox_locations.svg`            | an SVG file describing the regions of the template to scan for marks |
| `sample_pic.jpg`                    | a picture of a filled record |


This command should take a few seconds to run. The `digitize` script will first call the `align` script to correct for shifts/skews/rotations in the target image (i.e. filled record) relative to the template image (i.e. blank record). Next `digitize` will call the `simpleomr` script to process the marks on the aligned record.  

Algorithm progress and diagnostics will be printed to console. Output files will be written to an `output/` directory. In it you will find:

| Output File                           | Description   |
| -------------                         |:--------------|
| `sample_pic_aligned.jpg`           | a transformation of `sample_pic.jpg`, aligned and cropped to match the orientation of `template.jpg` |
| `sample_pic_matched.jpg`           | a diagnostic image showing the shared features used by the `align` script to calculate the re-alignment |
| `sample_pic_omr_classification.txt`| text output of the `simpleomr` script, including scores for each checkbox classification |
| `sample_pic_omr_debug.png`             | visual output of the `simpleomr` script |


To give a sense of the robustness of the alignment process and accuracy of the OMR algorithm we've included some example input and output in the `example/` directory. The directory `example/phone_pics/output/` contains the
output of processing each corresponding image in  `example/phone_pics/input`. Similarly `example/bad_scans/output/` contains the output of processing each corresponding image in  `example/bad_scans/input` and `example/good_scans/input` contains the output of processing each corresponding image in `example/good_scans/input` (in the case of `good_scans/` no re-alignment was necessary so only the OMR script was run). As you might expect, the results are better when scans are used rather than pictures. However there is still a lot of improvements to be made to  the alignment and mark recognition algorithms. Stay tuned :)




Walkthrough
============

Step 1: Alignment
-----------------

1. We start with a clean scan of a blank, unfilled medical record (`example/template.jpg`).
![](https://github.com/sdrp/digitize-mtc/blob/master/example/template.jpg)

2. Next we get a scan or picture of a filled medical record. The filled record will likely be rotated/skewed/shifted relative to the template. We don't expect anything near perfect in a clinical setting, i.e. the "real world". The sample picture below (`example/phone_pics/input/sample_pic.jpg`) was taken on an iPhone 4 (circa 2010) without flash.
![](https://github.com/sdrp/digitize-mtc/blob/master/example/phone_pics/input/sample_pic.jpg)

3. Feed the `align` script the two images above. It will calculate a re-alignment of sample image that orients the pictured record based on the template scan. The script will output the re-aligned sample (`output/sample_pic_aligned.jpg`), as well as a debug image displaying the features it used to calculate the re-alignment (`output/sample_pic_matched.jpg`).
![](https://github.com/sdrp/digitize-mtc/blob/master/example/phone_pics/output/sample_pic_matched.jpg)
![](https://github.com/sdrp/digitize-mtc/blob/master/example/phone_pics/output/sample_pic_aligned.jpg)


Step 2: Mark Recognition
------------------------

1. Now that we have an aligned input image, we need to pick out the the areas we want to target for mark recognition. Using an image editor we load the template image (`example/template.jpg`) and draw rectangles around the checkboxes we are interested in. After that, we save the result as an SVG file (`example/checkbox_locations.svg`).
![](https://github.com/sdrp/digitize-mtc/blob/master/example/checkbox_locations.svg)

2. Finally we feed the `simpleomr` script the aligned image along with the SVG file containing the checkbox locations. The script outputs a text file with results (`output/sample_pic_omr_classification.txt`) as well as a visual representation of its results (`output/sample_pic_omr_debug.png`). Green represents boxes that the script determined were checked. Red
represents empty (unchecked) boxes, and orange means that the script was not
able to make a confident guess.
![](https://github.com/sdrp/digitize-mtc/blob/master/example/phone_pics/output/sample_pic_omr_debug.png)



Credits
=======
The alignment method used was inspired by this post from Satya Mallik on LearnOpenCV (https://www.learnopencv.com/image-alignment-feature-based-using-opencv-c-python/)

The OMR script started as a fork of RescueOMR (https://github.com/EuracBiomedicalResearch/RescueOMR) created by Yuri D'Elia at EURAC, distributed under GNU AGPLv3+.
