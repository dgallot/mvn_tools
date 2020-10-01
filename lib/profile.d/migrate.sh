function migrate_from_svn_step_1() 
{
    cd ~/workspace-all
    gogs-clone-all.sh
    > missing.parents
    mvn_ids -n -p | awk ' { print $3 } ' | sort | uniq  > ~/workspace-all/parents
    cat ~/workspace-all/parents | while read n; do
      c=$( mvn_find $n | wc -l )
      if (( $c == 0 )); then
        echo "[Not Found] : $n"
        echo "$n" >> missing.parents
      else
        echo "[Found    ] : $n"
      fi
    done
}


function migrate_from_svn_step_2() 
{
    org=esb-parents
    cat ~/workspace-all/missing.parents | while read n; do
      migrate_from_svn esb-parents $n
    done
}


function migrate_from_svn()
{
   org=$1
   n=$2
      cd ~/svn/svn-clone/trunk   
      comment=$( printf "Migrated from svn $n \n" )
      projectname=$( basename $n )
      c=$( cat ~/workspace-all/missing.parents | while read p; do basename $p; done | grep ^${projectname}\$ | wc -l )
      if (( $c > 1 )); then
        projectname="$( basename $( dirname $n | tr  '.' '/' ))-${projectname}"
      fi
      c=$( cat ~/workspace-all/missing.parents | while read p; do basename $p; done | grep ^${projectname}\$ | wc -l )
      echo "$n : Project name : $projectname ( $c ) "
      c=$( mvn_find $n | wc -l )
      if (( $c != 1 )); then
        echo "Error $n not found or duplicate"
      else
        mvn_cd $n
        echo "  $(pwd)"
      fi  
      rm -rf .git
      gogs_url=$( gogs-create-repository.py -o $org -n $projectname -d "$comment" )      
      if (( $? != 0 )); then 
        echo "  [Gog-init] Error: $gogs_url "        
      else  
        echo "  [Gog-init] Project created $org/$projectname : [$gogs_url]."
      fi
      git init 2>&1 | prefix "  [Git-init] "
      git add pom.xml  2>&1 | prefix "  [Git-add] "
      git_add_update_file_to_root "Jenkinsfile" 2>&1 | prefix "  [Git-add] "
      git_add_update_file_to_root ".gitignore"  2>&1 | prefix "  [Git-add] "    
      git add Jenkinsfile  2>&1 | prefix "  [Git-add] "
      git add .gitignore  2>&1 | prefix "  [Git-add] "
      git commit -m '[ESBB-1050] Initial commit' 2>&1 | prefix "  [Git-add] "
      git remote add origin ${gogs_url} 2>&1 | prefix "  [Git-remote] "
      git push -u origin master 2>&1 | prefix "  [Git-push] "
      git branch develop 2>&1 | prefix "  [Git-branch] "
      git push -u origin develop 2>&1 | prefix "  [Git-push] "
      rm -rf .git
}

