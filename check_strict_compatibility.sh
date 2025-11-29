#!/bin/bash
if tsc --noEmit --strict "$1" 1>/dev/null 2>/dev/null ; then strict_ok=0; else strict_ok=1; fi
if tsc --noEmit "$1" 1>/dev/null 2>/dev/null ; then nostrict_ok=0; else nostrict_ok=1; fi
if [ $strict_ok -eq 0 ] && [ $nostrict_ok -ne 0 ]; then
  echo "Bug found in $1: strict succeeds but non-strict fails"
fi
