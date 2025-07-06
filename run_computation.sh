#!/bin/bash
export NIWA_API_KEY="REMOVED"

# Activate conda env
eval "$(conda shell.bash hook)"
conda activate coastsat_stencila_env

# navigate to the coastsat project directory
cd CoastSat

# Run your workflow or Jupyter notebook
jupyter nbconvert --to notebook --execute --inplace tidal_correction.ipynb linear_models.ipynb

conda deactivate