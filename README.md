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


Getting Started
===============
To get a feel for how the scripts works, run the following line:

`./bin/digitize ./example/template.jpg ./example/checkbox_locations.svg ./example/bad_scans/input/shift_skew_cutoff.jpg`


| Parameter                           | Description   |
| -------------                       |:--------------|
| `digitize`                          | an orchestration script that will call `align` and `simpleomr` in succession |
| `template.jpg`                      | a clean scan of a blank, unfilled record |
| `checkbox_locations.svg`            | an SVG file describing the regions of the template to scan for marks |
| `sample_scan.jpg`             | a scan of a filled record |


It should take a few seconds to run. The `digitize` script will first call the `align` script to correct for shifts/skews/rotations in the target image (i.e. filled record) relative to the template image (i.e. blank record). Next it calls the `simpleomr` script to process the marks on the filled record.  

Algorithm progress and diagnostics will be printed to console. Output files will be written to a `output/` directory. In it you will find:

| Parameter                           | Description   |
| -------------                       |:--------------|
| `sample_scan_aligned.jpg`           | a transformation of the `sample_scan.jpg`, aligned to match the orientation of `template.jpg` |
| `sample_scan_matched.jpg`           | a diagnostic image showing the shared features used by the `align` script to calculate the re-alignment |
| `sample_scan_omr_classification.txt`| text output of the `simpleomr` script, including scores for each classification |
| `sample_scan_omr_debug.png`             | visual output of the `simpleomr` script |

The directory `example/bad_scans/output/` contains the
output of processing each corresponding image in  `example/bad_scans/output`, and will give you a sense of the robustness of the alignment process and accuracy of the OMR algorithm.





Walkthrough
============

Step 1: Alignment
-----------------

1. We start with a clean scan of a blank, unfilled medical record (`example/template.jpg`).
![](https://github.com/sdrp/digitize-mtc/blob/master/example/template.jpg)

2. Next we get a scan of filled medical record (`example/bad_scans/input/sample_scan.jpg`). This scan will likely be rotated/skewed/shifted due to imprecision during "real world" use (ex. in a clinical setting).
![](https://github.com/sdrp/digitize-mtc/blob/master/example/bad_scans/input/sample_scan.jpg)

3. Feed the `align` script the two images above. It will calculate a re-alignment of sample scan that orients it based on the template record. The script will output the re-aligned sample (`output/sample_scan_aligned.jpg`), as well as a debug image displaying the features it used to calculate the alignment (`output/sample_scan_matched.jpg`).
![](https://github.com/sdrp/digitize-mtc/blob/master/example/bad_scans/output/sample_scan_matched.jpg)
![](https://github.com/sdrp/digitize-mtc/blob/master/example/bad_scans/output/sample_scan_aligned.jpg)


Step 2: Mark Recognition
------------------------

1. Now that we have an aligned scan, we need to pick out the the areas we want to target for mark recognition. Using an image editor we draw rectangles around the checkboxes we are interested in, and save the result as an SVG file (`example/checkbox_locations.svg`).
![](https://github.com/sdrp/digitize-mtc/blob/master/example/checkbox_locations.svg)

2. Finally we feed the `simpleomr` script the aligned scan, along with the SVG file containing the checkbox locations. The script outputs a text file with results (`output/sample_scan_omr_classification.txt`) as well as a visual representation of its results (`output/sample_scan_omr_debug.png`). Green represents boxes that the script determined were checked. Red
represents empty (unchecked) boxes, and orange means that the script was not
able to make a confident guess.
![](https://github.com/sdrp/digitize-mtc/blob/master/example/bad_scans/output/sample_scan_omr_debug.png)



Credits
-------
The alignment method used was inspired by this post from Satya Mallik on LearnOpenCV (https://www.learnopencv.com/image-alignment-feature-based-using-opencv-c-python/)

The OMR script started as a fork of RescueOMR (https://github.com/EuracBiomedicalResearch/RescueOMR) created by Yuri D'Elia at EURAC, distributed under GNU AGPLv3+.
