#!/bin/zsh
set -eu
# Calls the reviewed packaged launcher; all GPU and payload guards remain active.
launcher_bundle="$HOME/Applications/EldenLosSantosPreview"
/opt/homebrew/Cellar/python@3.14/3.14.7/Frameworks/Python.framework/Versions/3.14/bin/python3.14 "$launcher_bundle/Tools/launch_owner.py" \
  --gpu-root /Users/midir/sm2-n1/_scratch/gpu \
  --expected-host Mac --auto-owner-reservation --check
