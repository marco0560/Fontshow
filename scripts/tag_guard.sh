#!/usr/bin/env bash
set -e

echo "== Tag Guard =="

git fetch --tags --force

for tag in $(git tag); do
    if ! git merge-base --is-ancestor "$tag" HEAD; then
        echo "ERROR: tag $tag is not ancestor of HEAD"
        exit 1
    fi
done

echo "OK: all tags consistent"
