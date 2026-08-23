#!/bin/bash
set -e

usage() {
  echo "Usage: $0 <source_dir> <target_dir> [subdir1 subdir2 ...]"
  echo "Create symlinks in target_dir pointing to subdirs in source_dir."
  echo "If no subdirs given, link all subdirs in source_dir."
  exit 1
}

[[ $# -lt 2 ]] && usage

src_dir="$1"
dst_dir="$2"
shift 2

[[ ! -d "$src_dir" ]] && echo "Error: source dir not found: $src_dir" && exit 1
[[ ! -d "$dst_dir" ]] && echo "Error: target dir not found: $dst_dir" && exit 1

if [[ $# -eq 0 ]]; then
  subdirs=$(ls -d "$src_dir"/*/ 2>/dev/null | xargs -n1 basename)
  set -- $subdirs
  [[ -z "$1" ]] && echo "No subdirs found in $src_dir" && exit 0
fi

for subdir in "$@"; do
  src_path="$src_dir/$subdir"
  dst_path="$dst_dir/$subdir"

  [[ ! -d "$src_path" ]] && echo "Skipping: $subdir is not a directory in $src_dir" && continue

  if [[ -e "$dst_path" ]]; then
    echo "Exists: $dst_path, skipping"
    continue
  fi

  ln -s "$src_path" "$dst_path"
  echo "Linked: $dst_path -> $src_path"
done
