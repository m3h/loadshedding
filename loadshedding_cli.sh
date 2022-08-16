#!/bin/bash
# Set working directory to script location
# Required since some path are specified relative
cd "${0%/*}" 
export PYTHONPATH=${PYTHONPATH}:../loadshedding-thingamabob
python3 loadshedding.py || :  # Continue regardless of errors
