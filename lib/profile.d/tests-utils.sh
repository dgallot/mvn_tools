envoi_centralise_send() {
  document=${1:-/Users/forem/Downloads/30238845_a36_04_ris_fr_2018-09-13-08-23-45.pdf}
  curl -v -u esb_perf_test:esb_perf_test -F pdf=@$document http://esb-dev.forem.be/services/Documents/EnvoiCentralise/documents
}

run_multiples() {
  times=$1
  shift
  if [[ "$1" == "" ]]; then
    echo "First parameter 'Times' is mandatory"
  fi
  for ((index=0;index<$times;index++)); do 
    echo -n "$index : " 
    "$@"
  done
}

    