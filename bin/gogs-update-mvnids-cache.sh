#!/bin/bash

.  ~/bin/profile

rm -rf cd /tmp/wrk-$$
mkdir -p /tmp/wrk-$$

cd /tmp/wrk-$$

echo "Fetching all gogs projects"

gogs-list.py | while read o n u; do
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

cd /tmp/wrk-$$
git clone git@gogs.esb.tecteo.intra:development/common-tools.git

echo "Caching ( develop ) mvn ids on gogs projects"
git_all checkout develop
mvn_ids -g > common-tools/var/mvn_ids.gogs.develop

echo "Caching ( master ) mvn ids on gogs projects"
git_all checkout master
mvn_ids -g > common-tools/var/mvn_ids.gogs.master

echo "Caching ( release ) mvn ids on gogs projects"
git_cmd_all git_checkout_release_branch
mvn_ids -g -b | grep " release" > common-tools/var/mvn_ids.gogs.release

grep -Po 'origin/\K(.*)'

cd common-tools/var
git checkout develop

git add ./mvn_ids.gogs*
git commit -m "Updated version of mvn_ids.gogs"
cd /tmp
rm -rf /tmp/wrk-$$

