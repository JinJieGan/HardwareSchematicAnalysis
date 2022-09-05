Hardware Schematic Diagram AI Analysis Project
====================================================

This project implements an AI and CV based hardware schematic diagram analyzer,
which first burst a PDF into pages and convert them to JPEG images, then recognize
the texts and analyze the content of them.

# Usage


To run demo:

```
usage: main.py [-h] [-p PAGES] input

positional arguments:
  input                 Input PDF file name

optional arguments:
  -h, --help            show this help message and exit
  -p PAGES, --pages PAGES
                        Indicate page range. use [a,b,...] for indicating a
                        set of page or "(a,b)" (please use quotation marks) to
                        indicate a page range (both side inclusive).
```

# Install

### Prerequisites

* pdftk (If you failed to install via a package manager, please download
standalone jar file (need JRE runtime) or native image file to the project folder from
[Project page](https://gitlab.com/pdftk-java/pdftk), and update your
installation type in config.py):
    ```python
    # Available choices: ["PackageMgr", "StandaloneJar", "NativeImage"]
    PDFTK_INSTALLATION_TYPE = "PackageMgr"
    ```
    If you downloaded the native pdftk image, be sure to grant executing permission with
    ```
    chmod +x pdftk
    ```
* ImageMagick

* conda (Follow install instructions on 
[Anaconda install instructions](https://docs.anaconda.com/anaconda/install/))

### Setup Steps

1. Clone the repository and navigate into the cloned repository:
    ```
    git clone ssh://<your_username>@ico-pae-gerrit.sh.intel.com:29418/openvino/ai_analyis
    mv ai_analyis ai_analysis
    cd ai_analysis
    ```

2. Init and update the submodule:
    ```
    git submodule update --init --recursive
    ```

3. Create a new virtual environment with Python 3.6.9, and activate it (recommended, optional):
    ```
    conda create -n hwsa-env python==3.6.9
    conda activate hwsa-env
    ```

4. Install dependencies:
    ```
    python -m pip install -U pip
    pip install -r requirements.txt 
    ```

5. Allow ImageMagick PDF coder to read/write (In refer to [Alex Vanderbist](https://alexvanderbist.com/2018/fixing-imagick-error-unauthorized/)):

    In /etc/ImageMagick-6/policy.xml (or /etc/ImageMagick/policy.xml) find the following line
    ```
    <policy domain="coder" rights="none" pattern="PDF" />
    ```
    and change it into:
    ```
    <policy domain="coder" rights="read|write" pattern="PDF" />
    ```
6. Example output
  
  ![image](https://user-images.githubusercontent.com/66105373/188462405-42924872-5eff-49f1-90c5-a7ab3aff510f.png)
