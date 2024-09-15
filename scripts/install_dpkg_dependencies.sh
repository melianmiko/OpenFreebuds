#!/usr/bin/env bash

apt install -y $(awk '
  /^(Build-)?Depends:/ || /^ / && deps {
    sub(/^[^ ]+: /, "")
    deps = 1
    dep_str = dep_str ", " $0
    next
  }
  { deps=0 }
  END {
    split(dep_str, dep_array, /[,|] */)
    for (d in dep_array) {
      dep = dep_array[d]
      gsub(/[^a-z0-9_.+-].*$/, "", dep)
      if (dep && !seen[dep]++) print dep
    }
  }' scripts/build_debian/debian/control)
