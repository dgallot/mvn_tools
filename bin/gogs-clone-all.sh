#!/bin/bash

.  ~/bin/profile

REF_HOST=tacceptance1

mkdir -p .cache
if [[ -f error.list ]]; then
  rm error.list
fi
echo "Caching gogs projects list"
gogs-list.py | sort > .cache/urls.gogs

if [[ "$1" != "" ]]; then
  instance=$1
  echo "Fetch mvn ids cached"
  git archive --remote=ssh://gogs.esb.tecteo.intra/development/common-tools.git HEAD var/mvn_ids.gogs | tar -x -O var/mvn_ids.gogs > .cache/mvn_ids.gogs
  echo "List all bundles from ${REF_HOST}"
  remote-list-bundle.py -H ${REF_HOST} -i $instance -F none | grep be.voo > .cache/${instance}_mvn_ids.gogs 
  remote-list-features-url.py -H ${REF_HOST} -i $instance -F none | grep be.voo | awk ' { print $2 }' | cut -f 1,2 -d '/' >> .cache/${instance}_mvn_ids.gogs
  cat .cache/${instance}_mvn_ids.gogs | cut -f 2 -d ' ' | cut -f 1,2 -d '/' | while read id; do 
    c=$( cat .cache/mvn_ids.gogs | grep " ${id}/" | wc -l )
    if [[ "$c" = 1 ]]; then
      giturl=$( cat .cache/mvn_ids.gogs | grep " ${id}/" | awk ' { print $3 }' )
      echo "Fetching ${id} : ${giturl}"
      ( git clone ${giturl} 2>&1 ) | prefix "  "
    else 
      echo "[ERROR] ${id} not found"       
      echo " ${id} " >> error.list
    fi    
  done
  if [[ -f error.list ]]; then
    echo "[ERROR] The following package has not been found"
    cat error.list
  fi
else
  echo "Fetching all gogs projects"
  cat .cache/urls.gogs | while read o n u; do
    echo "Imporing $o/$n : $u"
    (
      mkdir -p $o 
      cd $o
      if [[ ! -d "${n}" ]]; then
        git clone -q -b develop ${u} 2>&1 | prefix "  [$n]"
        rc=${PIPESTATUS[0]}
        if (( $rc != 0 )); then
          echo "Trying master branch" | prefix "  [$n]"
          git clone -q -b master ${u} 2>&1 | prefix "  [$n]"
        fi
      else
        ( cd $n; git pull ) 2>&1 | prefix "  [$n]"
      fi
    )
  done
fi

echo "Caching mvn ids on gogs projects"
( 
  mvn_ids
) > .cache/mvn_ids.gogs

git_cmd_all git_add_mandatory_files
