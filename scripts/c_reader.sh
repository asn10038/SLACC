#!/bin/bash

#SBATCH --job-name codeseer
#SBATCH -N 16
#SBATCH -n 64
#SBATCH -p opteron
# Use modules to set the software environment

python readers/c_reader.py 64
