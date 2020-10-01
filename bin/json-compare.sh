#!/bin/bash

JQ=/usr/local/bin/jq
BN=$(basename $0)

function help {
  cat <<EOF

Syntax: $0 file1 file2

The two files are assumed each to contain one JSON entity.  This
script reports whether the two entities are equivalent in the sense
that their normalized values are equal, where normalization of all
component arrays is achieved by recursively sorting them, innermost first.

This script assumes that the jq of interest is $JQ if it exists and
otherwise that it is on the PATH.

EOF
  exit
}

if [ ! -x "$JQ" ] ; then JQ=jq ; fi

function die     { echo "$BN: $@" >&2 ; exit 1 ; }

if [ $# != 2 -o "$1" = -h  -o "$1" = --help ] ; then help ; exit ; fi

test -f "$1" || die "unable to find $1"
test -f "$2" || die "unable to find $2"

$JQ -r -n --argfile A "$1" --argfile B "$2" -f <(cat<<"EOF"
# Apply f to composite entities recursively, and to atoms
def walk(f):
  . as $in
  | if type == "object" then
      reduce keys[] as $key
        ( {}; . + { ($key):  ($in[$key] | walk(f)) } ) | f
  elif type == "array" then map( walk(f) ) | f
  else f
  end;

def normalize: walk(if type == "array" then sort else . end);

# Test whether the input and argument are equivalent
# in the sense that ordering within lists is immaterial:
def equiv(x): normalize == (x | normalize);

if $A | equiv($B) then empty else "\($A) is not equivalent to \($B)" end

EOF
)
