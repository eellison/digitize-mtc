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

`>> ./simpleomr -d debug.png example/checkbox_locations.svg example/input/filled_form_1.png`

*debug.png*: the script's output location
*checkbox_locations.svg*: an SVG file containing the regions of the
input document to scan (determined by <rect> tags within its XML)
*example/input/filled_form_1.png*: input file for processing, representing
a filled medical record

It might take 15-25 seconds to run given that there is currently
no optimization in the algorithm. Results will be printed to console.
Opening *debug.png* will show a visual representation of the output.
Green represents checkboxes that the script determined were checked. Red
represents empty (unchecked) boxes, and orange means that the script was not
able to make a confident guess. The directory `example/output/` contains the
output of processing each corresponding image in  `example/input/`,
all with the same input parameters.



**Note:** Settings and tolerances are tuned for 300 dpi gray-scale documents
at the moment.

Started as a fork of RescueOMR (https://github.com/EuracBiomedicalResearch/RescueOMR) created by Yuri D'Elia at EURAC, distributed under GNU AGPLv3+.
