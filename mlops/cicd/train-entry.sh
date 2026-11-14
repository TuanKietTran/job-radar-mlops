#!/bin/sh
# Training entry point: run the training module when present, else the dry-run guard.
if [ -f mlops/training/train.py ]; then
  exec python3 mlops/training/train.py
elif [ -f mlops/training/main.py ]; then
  exec python3 mlops/training/main.py
else
  echo 'train entry point absent, dry-run guard exits 0'
fi
