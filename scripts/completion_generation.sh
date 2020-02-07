#!/bin/zsh
_YOUTUBETOTV_COMPLETE=source_zsh youtubetotv > zsh_completion_source.sh
git add zsh_completion_source.sh
_YOUTUBETOTV_COMPLETE=source youtubetotv > bash_completion_source.sh
git add bash_completion_source.sh

