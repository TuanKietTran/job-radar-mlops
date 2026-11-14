#!/bin/sh
# Build the API and training images and record the outcome.
# Usage: sh mlops/cicd/build.sh
# Set BUILD_LOG to append the outcome lines to a file as well.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$ROOT"
LOG=${BUILD_LOG:-}
record() {
  printf '%s\n' "$1"
  if [ -n "$LOG" ]; then
    printf '%s\n' "$1" >> "$LOG"
  fi
}
build_one() {
  name=$1
  file=$2
  tag=$3
  if docker build -f "$file" -t "$tag" .; then
    image_id=$(docker image inspect -f '{{.Id}}' "$tag")
    record "build: $name ok tag $tag image $image_id"
  else
    record "build: $name failed"
    return 1
  fi
}
status=0
build_one api mlops/cicd/Dockerfile.api job-radar-api:local || status=1
build_one train mlops/cicd/Dockerfile.train job-radar-train:local || status=1
record "build: done with status $status"
exit "$status"
