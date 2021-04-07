#!/bin/bash

set -eux

OUTPUT_FILE=icecream_${TOX_ENV_NAME}.py

stickytape stickytape_entry.py \
  --add-python-path .. \
  --add-python-module pygments.formatters.terminal256 \
  --add-python-module pygments.lexers.python \
  --add-python-module icecream.__version__ \
  --add-python-path $(python site_packages_path.py) \
  --output-file $OUTPUT_FILE

ls -lh $OUTPUT_FILE
cp $OUTPUT_FILE single_file_icecream.py

python test_single_file_icecream.py
