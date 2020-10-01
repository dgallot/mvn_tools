
changes_add()
{
  git_root=$( locate_git_root )
  if (( $? != 0 )); then
    echo "Not in  a git repository"
    return 0
  fi
  (
    cd $git_root
    local project=""
    if [[ "$1" = "-p" ]]; then
      shift
      project="$1"
      shift
    fi
    changes_file=$( locate_changes_file -p "$project" )    
    if (( $? != 0 )); then
      return 1
    fi
    (
        mvn_id=$( mvn_id -n )
        c=$( cat ${changes_file} | grep "$mvn_id" | wc -l  )
        if (( c == 0 )); then
          echo "Adding '${mvn_id}' in ${changes_file}"
        else
          echo "'${mvn_id}' Already in ${changes_file}"
        fi
        echo "${mvn_id}" >> ${changes_file}
    )
  )
}

#H changes_start workspace_location project_id
#H   project_id is either a jira id or a release identifier
changes_start()
{
  workspace=$1
  id=$2
  if [[ "$1" == "" ]]; then
    echo "No direcftory provided, the root worspace location is mandatory"
    return 1
  fi
  if [[ "$id" == "" ]]; then
    echo "Please provide a unique identifier for the changes tracking."
    return 1
  fi
  if [[ ! -d "$1" ]]; then
    echo "$1 is not a directory"
    return 1
  fi
  if [[ -f $workspace/$id.changes ]]; then
    echo "Change file $workspace/$id.changes already exists"
    return 1
  fi
  touch $workspace/$id.changes
}

#H changes_infos -r project_id
#H - resume all changes
#H   -r recursive
#H   project_id is either a jira id or a release identifier
changes_infos()
{
  if [[ "$1" == "-r" ]]; then
    recursive=true
  else
    recursive=false
  fi
  
 changes_file=$( locate_changes_files . )
 if (( $? != 0 )); then
   return 1
 fi
    (
      home=$( dirname $changes_file )  
      cd $home
      cat $( basename $changes_file ) | filter_empty_comment | while read n v; do
        if [[ "$n" = "" ]]; then
          continue
        fi
        path=$( mvn_find $n 2>/dev/null | head -1 | awk -e '{print $1}' )
        (
          if [[ "$path" = "" ]]; then
            path="Not found"
            id="NA"
            branch="NA"
            echo -e "${path}[${branch}]\t${n}/N-A"
          else
            id=$( cd $path; mvn_id $path )
            branch=$( cd $path; git rev-parse --abbrev-ref HEAD ) 
            echo -e "${path}[${branch}]\t${id}"
            if [[ "$recursive" = "true" ]]; then
              ( 
                cd $path;
                mvn_ids 
              ) | grep -v ${id} | prefix "  "
            fi
          fi
        )
      done
   )
}


changes_cmd()
{    
  local project=""
  local force="false"
  if [[ "$1" = "-p" ]]; then
    shift
    project="$1"
    shift
  fi
  if [[ "$1" = "-f" ]]; then
    shift
    force="true"
  fi
    changes_file=$( locate_changes_file -p "$project" .  )  
    if (( $? != 0 )); then
      return 1
    fi
    (
      home=$( dirname $changes_file )
      cd $home
      cat $( basename $changes_file ) | filter_empty_comment | while read n v; do
        if [[ "$n" = "" ]]; then
          continue
        fi
        path=$( mvn_find $n 2>/dev/null | head -1 | awk -e '{print $1}' )
        (
          if [[ "$path" = "" ]]; then
            echo "Maven project for $n not found" >&2            
            return 1
          else
            (
              echo "[$path] : $n"
              cd $path
              prefix="[$( mvn_id )]"
              "$@" | prefix ${prefix}
              rc=${PIPESTATUS[0]}
              return $rc
            )      
            rc=$?
            if (( $rc != 0 )); then
              if [[ "$force" = "true" ]]; then
                return 0
              else
                return 1
              fi
            fi
          fi
        )
        rc=$?
        if (( $rc != 0 )); then
          return 1
        fi        
      done
   )
}

changes_mvn()
{    
  local project=""
  local force="false"
  if [[ "$1" = "-p" ]]; then
    shift
    project="$1"
    shift
  fi
  if [[ "$1" = "-f" ]]; then
    shift
    force="true"
  fi  
    changes_file=$( locate_changes_file -p "$project" .  )  
    if (( $? != 0 )); then
      return 1
    fi
    (
      home=$( dirname $changes_file )
      cd $home
      cat $( basename $changes_file ) | filter_empty_comment | while read n v; do
        if [[ "$n" = "" ]]; then
          continue
        fi
        path=$( mvn_find $n 2>/dev/null | head -1 | awk -e '{print $1}' )
        (
          if [[ "$path" = "" ]]; then
            echo "Maven project for $n not found" >&2            
            return 1
          else
            (
              echo "[$path] : $n"
              cd $path
              prefix="[$( mvn_id )]"
              mvn "$@" | prefix ${prefix}
              rc=${PIPESTATUS[0]}
              return $rc
            )      
            rc=$?
            if (( $rc != 0 )); then
              if [[ "$force" = "true" ]] ; then
                return 0
              else
                return 1
              fi
            fi
          fi
        )
        rc=$?
        if (( $rc != 0 )); then
          return 1
        fi        
      done
   )
}

#H locate_changes_files
#H    locate all change tracking files 
locate_changes_files() {
  path=${1:-.}
  found=0
  locate_changes_files_r $path
}

locate_changes_files_r() {
  path=$1
  c=$( ls $path/*.changes 2>/dev/null | wc -l )
  if (( $c > 0 )); then
    found=$(( found + $c ))
    ls -1 $path/*.changes
  fi
  if [[ "$( realpath $path/.. )" = "/" ]]; then
    if (( $found == 0 )); then
      echo "No file '[.../]*.changes' found" >&2
      return 1
    fi
    return 0
  fi
  if [ "$path" = "." ]; then
      locate_changes_files_r ..
    else
      locate_changes_files_r $path/..
  fi
}

locate_changes_file() {
  local project=""
  if [[ "$1" = "-p" ]]; then
    shift
    project="$1"
    shift
  fi
  path=${1:-.}
  c=$( ls $path/*.changes 2>/dev/null | wc -l )
  if (( $c > 0 )); then
    if [[ "$project" = "" ]]; then    
      if (( $c == 1 )); then
        echo $path/*.changes
      else
        echo "Multiple changes files found '$( join_by ', ' $( remove_ext $( basenames $path/*.changes ) ) )'. Please provide the -p argument" >&2
        return 1
      fi
    else
      c=$( ls $path/${project}.changes 2>/dev/null | wc -l )
      if (( $c == 1 )); then
        echo $path/${project}.changes
      else
        echo "No changes files found for ${project}. Available files are '$( join_by ', ' $( remove_ext $( basenames $path/*.changes ) ) )'" >&2
        return 1
      fi
    fi
    return 0
  else
    if [ "$( realpath $path/.. )" = "/" ]; then
      echo "File '[.../]*.changes' required" >&2
      return 1
    fi
    if [ "$path" = "." ]; then
      locate_changes_file -p "$project" ..
    else
      locate_changes_file -p "$project" $path/..
    fi
  fi
}

#changes_check_version
changes_check_version() {
 cur_pwd=$( pwd )
 changes_file=$( locate_changes_files . )
 current_branch=$( git_current_branch )
 echo "Checking $(mvn_id) [$current_branch] against ${changes_file}"
 if (( $? != 0 )); then
   return 1
 fi
 (
   home=$( dirname $changes_file )  
   cd $home
   cat $( basename $changes_file ) | filter_empty_comment | while read n v; do
    if [[ "$n" = "" ]]; then
        continue
    fi
    path=$( mvn_find $n 2>/dev/null | head -1 | awk -e '{print $1}' )
    (
        if [[ "$path" = "" ]]; then
            path="Not found"
            id="NA"
            branch="NA"
            echo -e "${path}[${branch}]\t${n}/N-A"
        else
            current_branch=$( cd $path; git_current_branch )
            id=$( cd $path; mvn_id -n )
            master_version=$( cd $path; git checkout master >/dev/null 2>/dev/null; mvn_id | cut -f 3 -d '/' ; git checkout $current_branch  >/dev/null 2>/dev/null )            
            pwd_path=$( cd $path; pwd )
            if [[ "$cur_pwd" != "$pwd_path" ]]; then
                echo -e "${path}[master]\t${id}/${master_version}"
                ( 
                    cd $path
                    mvn_ids -n | while read path id; do
                        mvn_version_tools=$( cd $cur_pwd; mvn-version-tools.py -b $id -q )
                        found=$( echo -n "$mvn_version_tools" | wc -w )
                        if (( $found > 0 )); then
                            echo "$mvn_version_tools"
                        fi
                    done
                ) | prefix "  "            
            fi
        fi
    )
    done
  )
}



