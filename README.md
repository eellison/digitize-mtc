# mae-tao-omr
an OMR-based tool that automates data extraction from scanned medical records


Dependencies
------------
- Python 3
- Python Imaging Library (PIL) (``python3-pil``, distributed as part of ``python3-Pillow``)
- Python lxml (``python3-lxml``)
- NumPy (``python3-numpy``)
- SciPy (``python3-scipy``)
- scikit-image (``python3-skimage``)


Getting Started
---------------
To get a feel for how the script works, run the following line:

`>> ./simpleomr example/checkbox_locations.svg example/input/filled_form_1.png output.txt -d output.png `

*checkbox_locations.svg*: an SVG file containing the regions of the
input document to scan (determined by <rect> tags within its XML); in this example is is a
blank copy of the clinic's antenatal record

*example/input/filled_form_1.png*: input file for processing, representing
a filled antenatal record

*output.txt*: path to which  the script will write TSV output

*output.png*: path to which the script will write visual debug output




It might take 15-25 seconds to run given that there is currently
no optimization in the algorithm. Results will be printed to console.
Opening *debug.png* will show a visual representation of the output.
Green represents boxes that the script determined were checked. Red
represents empty (unchecked) boxes, and orange means that the script was not
able to make a confident guess. The directory `example/output/` contains the
output of processing each corresponding image in  `example/input/`,
all with the same input parameters.


General Idea
------------
1. We start with a blank version of a medical record. Using an image
editor we draw rectangles around the checkboxes we are interested in, and save
the result as an SVG file.
![](https://github.com/sdrp/digitize-mtc/blob/master/example/checkbox_locations.svg)

2. Next we feed the script a filled-out version of the record. This image
should be a 300 dpi grayscale scan. It's worth tinkering with the contrast of the input image and the thresholds used by the script to see what configuration yields
the best results. For example, the document below had its contrast increased after scanning to improve the OMR accuracy.
![](https://github.com/sdrp/digitize-mtc/blob/master/example/input/filled_form_1.png)

3. The script outputs a visual representation of its results.
![](https://github.com/sdrp/digitize-mtc/blob/master/example/output/form_1_processed.png)



Credits
-------
Started as a fork of RescueOMR (https://github.com/EuracBiomedicalResearch/RescueOMR) created by Yuri D'Elia at EURAC, distributed under GNU AGPLv3+.
