#!/usr/bin/env bash

pkg=$1
ver=$2

conda remove -q -y -n tmp --all
conda create -q -y -n tmp pip "${pkg}==${ver}" python=3.7
if [[ "$?" == "0" ]]; then
  source activate tmp
  echo "conda env: "$CONDA_DEFAULT_ENV
  pip check
  rm -f pip_check_results.txt
  pip check >& pip_check_results.txt
  conda deactivate
  conda remove -q -y -n tmp --all
fi
