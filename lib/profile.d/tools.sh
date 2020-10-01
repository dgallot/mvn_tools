#H
#H
#H Misc tools
#H
#H
#H tools_find_duplicate file awk_id_expression awk_group_expression filter
#H    Allows to find duplicate entries in text file
#H      file the file to process
#H      awk_id_expression The awk expression to extract the identifier of the line
#H      awk_group_expression The awk expression to extract element to print in the group line
#H      filter a grep expression to filter the file before processing
#H
#H    Example:
#H      tools_find_duplicate ~/var/exports.tacceptance3.frontoffice '{ print $3 }' '{ print $1 "/" $2 }' be.voo
#H

function tools_find_duplicate()
{
    file=$1
    awk_id_expression=$2
    awk_group_expression=$3
    filter=$4
    if [[ "$filter" = "" ]]; then
      filter="."
    fi
    cat $file | sort | uniq | awk "${awk_id_expression}" | grep "$filter" | sort | uniq -d | while read id; do
        c=$( cat $file | awk "${awk_id_expression}" | grep -x "$id" | wc -l )
        groups=$( echo $( cat $file | grep $id | awk "${awk_group_expression}" | sort | uniq ) )
        echo "$(printf '%03d' $c) | $id | $groups"
        
    done
}


function tools_filter_on_fields()
{
    file=$1
    awk_field_extractor=$2    
    filter=$3
    filter_option=$4
    cat $file | while read line; do
        c=$( echo "$line" | awk "$awk_field_extractor" | grep $filter_option "$filter" | wc -l )
        if (( $c > 0 )); then
            echo "$line"  
        fi        
    done
}


function tools_filter_on_file_lookup()
{
    file=$1
    lookup_file=$2
    awk_file_id_extractor=$3
    awk_lookup_id_filer=$4
    expression=' > 0'
    cat $file | while read line; do        
        id=$( echo "$line" | awk "$awk_file_id_extractor" )
        c=$( tools_filter_on_fields "$lookup_file" "$awk_lookup_id_filer" "$id" | wc -l )        
        res="$( expr $c $expression )"
        if (( $res == 1 )); then
            echo "$line"
        fi        
    done
}


locate_parent_file() {
  file=$1
  path=${2:-.}  
  c=$( ls -d $path/$file 2>/dev/null | wc -l )
  if (( $c > 0 )); then
    echo $path
    return 0
  else
    if [ "$( realpath $path/.. )" = "/" ]; then
      echo "File '[.../]$file' required" >&2
      return 1
    fi
    if [ "$path" = "." ]; then
      locate_parent_file $1 ..
    else
      locate_parent_file $1 $path/..
    fi
  fi
}
