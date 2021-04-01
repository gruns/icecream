#!/bin/bash

set -eux

stickytape stickytape_entry.py \
  --add-python-path .. \
  --add-python-module pygments.formatters.terminal256 \
  --add-python-module pygments.lexers.python \
  --add-python-module icecream.__version__ \
  --add-python-path $(python site_packages_path.py) \
  --output-file single_file_icecream.py

ls -lh single_file_icecream.py

python test_single_file_icecream.py
