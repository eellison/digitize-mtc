# mae-tao-omr
a OMR-based tool that automates data extraction from scanned medical records


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
`>> ./simpleomr -d debug.png example_files/marks.svg example_files/filled_2.png`

It might take as many as 20 seconds to run given that there is currently
no optimization in the algorithm. Results will be printed to console.
Opening *debug.png* will show a visual representation of what the algorithm saw.
The OMR regions are determined by "rect" tags located in the XML
representation of the *marks.svg* file.


**Note:** Settings and tolerances are tuned for 300 dpi gray-scale documents

Started as a fork of RescueOMR (https://github.com/EuracBiomedicalResearch/RescueOMR) created by Yuri D'Elia at EURAC, distributed under GNU AGPLv3+.
