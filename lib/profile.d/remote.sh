ALL_CONTAINERS="esb nicedevice wfm bss cataloginventory frontoffice options oss printhandling sapconnector terranova"

#H export_find_duplicate_exports_and_usage host instance [ -o ]
#H  -o Offline mode

function export_find_duplicate_exports_and_usage()
{
  host=$1
  instance=$2
  if [[ "$host" = "" ]]; then
    echo "Host is missing"
    h export_find_duplicate_exports_and_usage
    return
  fi
  if [[ "$instance" = "" ]]; then
    echo "Instance is missing"
    h export_find_duplicate_exports_and_usage
    return
  fi
  shift
  shift
  if [[ "$1" != "-o" ]]; then
    echo "remote-list-exports-bundle.py -H $host -i $instance"
    remote-list-exports-bundle.py -H $host -i $instance > exports.$host.$instance
  else
    echo "Using cached file exports.$host.$instance"
    if [[ ! -f "exports.$host.$instance" ]]; then
      echo "File exports.$host.$instance not found"
      return
    fi
  fi
  tools_find_duplicate exports.$host.$instance '{ print $3 }' '{ print $1 "/" $2 }' be.voo > exports.duplicate.$host.$instance 
  if [[ "$1" != "-o" ]]; then
    echo "remote-list-imports-bundle.py -H $host -i $instance"
    remote-list-imports-bundle.py -H $host -i $instance > imports.$host.$instance
  else
    echo "Using cached file imports.$host.$instance"
    if [[ ! -f "imports.$host.$instance" ]]; then
      echo "File imports.$host.$instance not found"
      return
    fi
  fi
  echo "Processing output"
  (
    echo "Package ProvidingArtifactId UsingArtifactId"
    cat  exports.duplicate.$host.$instance | awk ' { print $3 } ' | while read package; do
      tools_filter_on_fields imports.$host.$instance '{ print $3 } ' "$package" '-x' | awk '{ print $3 "/" $4  " " $1 "/" $2 } ' | while read line; do
        packagever=$( echo "$line" | awk '{ print $1 }' )
        using_artifactId=$( echo "$line" | awk '{ print $2 }' )
        providing_artifactId=$( cat exports.$host.$instance | tr -d '"' | awk '{ print $3 "/" $4 " " $1 "/" $2 }' | grep -F "$packagever" | awk ' { print $2 } ' )
        echo "$packagever $providing_artifactId $using_artifactId"
      done
    done 
  ) | tee duplicate_exports_and_usage.$host.$instance
  echo "Saved in duplicate_exports_and_usage.$host.$instance"
}


function export_find_duplicate_exports_and_usage_all_container() {
  host=$1
  if [[ "$host" = "" ]]; then
    echo "Host is missing"
    return
  fi  
  for instance in ${ALL_CONTAINERS}; do
    export_find_duplicate_exports_and_usage "${host}" ${instance} | prefix "[${instance}]"
  done
}