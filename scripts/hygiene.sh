#!/bin/bash
# Check the repo for banned tokens.
# Run from any directory with: bash scripts/hygiene.sh
# Exit 0 when clean, exit 1 when a banned token is found.
set -u
set -f
ROOT=$(cd $(dirname $0)/.. && pwd)
cd $ROOT
FOUND=0
WORD_PATTERNS=(
'[M]use'
'[f]leet'
'[l]ab'
'[c]mdr'
'Co-Authored-[B]y'
'Generated.[w]ith'
'[s]upercharge'
'[s]eamless'
'[u]nlock'
'[m]agic'
'[g]ame-changing'
'[A]I-[p]owered'
'[p]i'
'[m]l-[a-z]'
)
PLAIN_PATTERNS=(
'/[U]sers/'
)
for pattern in ${WORD_PATTERNS[@]}; do
  if grep -r -n -I -i -w -E -e $pattern --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ --exclude-dir=.tox --exclude-dir=node_modules --exclude-dir=.terraform --exclude-dir=.pytest_cache --exclude-dir=evidence --exclude=hygiene.sh --exclude=sbom.spdx.json --include=*.py --include=*.md --include=*.yml --include=*.yaml --include=*.sh --include=*.txt --include=Makefile --include=Dockerfile* --include=.gitignore .; then
    FOUND=1
  fi
done
for pattern in ${PLAIN_PATTERNS[@]}; do
  if grep -r -n -I -i -E -e $pattern --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ --exclude-dir=.tox --exclude-dir=node_modules --exclude-dir=.terraform --exclude-dir=.pytest_cache --exclude-dir=evidence --exclude=hygiene.sh --exclude=sbom.spdx.json --include=*.py --include=*.md --include=*.yml --include=*.yaml --include=*.sh --include=*.txt --include=Makefile --include=Dockerfile* --include=.gitignore .; then
    FOUND=1
  fi
done
if [ $FOUND -eq 0 ]; then
  echo 'hygiene: pass'
  exit 0
fi
echo 'hygiene: fail'
exit 1
