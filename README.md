# Digitiz
an OMR tool that automates data extraction from paper records


Dependencies
============
- Python 3
- Python Imaging Library (PIL) (``python3-pil``, distributed as part of ``python3-Pillow``)
- Python lxml (``python3-lxml``)
- NumPy (``python3-numpy``)
- SciPy (``python3-scipy``)
- scikit-image (``scikit-image``)
- opencv (``opencv-contrib-python``)
- onnxruntime (``onnxruntime``)
- pathlib (``pathlib``)
- flask (``flask``)

All of these can be installed used `pip` or `conda`. If you are planning to plug in
an external UVC-enabled USB camera to use the live alignment feature, make sure
to download ``opencv-contrib-python``, since the package hosted under
``opencv-contrib`` does not provide video device support via OpenCV.


Getting Started
===============
To get a feel for how the scripts works, start the server using the following line:

```
python backend/server.py
```

Find Out More
=============
Find out more about our project and vision at https://sdrp.github.io/digitize-mtc/.
