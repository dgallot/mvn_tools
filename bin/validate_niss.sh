#!/bin/bash
while read n; do 
  if [[ ${#n} -eq 0 ]]; then
    continue
  fi
  if [[ ${#n} -ne 11 ]]; then
    echo "$n : Invalid lenght ${#n}"
  else 
    raw=${n:0:9}
    niss_mod=${n:9:2}
    year=${n:0:2}
    if (( $year > 30 )); then
      mod=$( expr $raw % 97)
    else
      mod=$( expr 2$raw % 97)
    fi
    if [[ ${niss_mod:0:1} = "0" ]]; then
      niss_mod=${niss_mod:1:1}
    fi
    val=$( expr 97 - $mod )
    if (( $val != $niss_mod )) ; then
      echo "$n : Invalid modulo expected $val ( 97 - $mod )"
    else
      echo "$n : ok"
    fi
  fi
done


