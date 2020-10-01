#!/usr/bin/env bash

#H 
#H Git Tools
#H -----------
#H - git_all
#H   Run a git command on all git repository found in sub directories
git_all()
{
  find . -name .git | while read n; do 
    d=$( dirname $n )
    echo $d
    ( cd $d; git "$@" ) | prefix "  "
  done
}

#H - git_remove_branch
#H   Remove a local and remote branch
git_remove_branch()
{
    if [[ "$1" = "" ]]; then
      echo "Missing branch to remove"
      retur 1
    fi
    git push origin --delete $1
    git branch -D $1
    git fetch --prune
}

#H - git_show_remote_urls
#    Show remote urls
git_show_remote_urls()
{
  git_all config --get remote.origin.url 
}

#H - gogs_clone_all <container>
#    Clone all gogs repository
gogs_clone_all()
{
  gogs-clone-all.sh $*
}
 
#H - git_set_default_branch
#H   Set default branch
git_set_default_branch()
{
  new_branche=$1
  current=$( cat .git/HEAD | cut -f 2 -d : | xargs -L 1 basename )
  branches=$( git branch -ar | grep -v HEAD | xargs -L 1 basename )
  if [[ "$current" = "$new_branche" ]]; then
    echo "Branch $new_branche is already the default."
    return
  else
    for b in $branches; do
      if [[ "$b" = "$new_branche" ]]; then
        echo "Setting $new_branche as the default."
        git remote set-head origin $new_branche 2>&1 | prefix "  "
        git symbolic-ref HEAD refs/heads/$new_branche 2>&1 | prefix "  "
        return 0
      fi
    done
  fi
  echo "Branch $new_branche can be set as default, branch not found."
}

#H - git_cmd_all
#H   Run a git command on all git repository found in sub directories
git_cmd_all()
{
  cmd=$1
  shift
  find . -name .git | while read n; do 
    d=$( dirname $n )
    echo $d    
    ( cd $d; $cmd "$@" ) | prefix "  "
  done
}


#H - git_create_default_branch
#H   Make sure
git_create_default_branch()
{
  url=$( git config --get remote.origin.url )
  echo -n "$url : "
  develop_exists=$( git ls-remote --heads 2>&1 | grep develop | wc -l )
  master_exists=$( git ls-remote --heads 2>&1 | grep master | wc -l )
  if (( $develop_exists == 0 )); then
    echo -n "branch develop not found. "
  else
    git checkout develop > /dev/null 2>&1
  fi
  if (( $master_exists == 0 )); then
    echo -n " branch Master not found. "
  else
    git checkout master > /dev/null 2>&1
  fi
  if (( $master_exists + $develop_exists >= 2 )); then
    echo "Branch develop and master exists."
  else
    echo "."
  fi
  if (( $develop_exists == 0 )); then
    git checkout -b develop 2>&1 | prefix "  [develop]"
    git push -u origin HEAD 2>&1 | prefix "  [develop]"
  fi
  if (( $master_exists == 0 )); then
    git checkout -b master 2>&1 | prefix "  [master]"
    git push -u origin HEAD 2>&1 | prefix "  [master]"
  fi
}


#H - git_extrat_changes <JiraId>
#H   Search the git log of all git repository 
git_extrat_changes() {
    jira_id=$1
    if [[ "$jira_id" = "" ]]; then
      echo "JiraId must be passed as first parameter"
      return
    fi
    rc=$( echo "$jira_id" | egrep [[:upper:]]+-[[:digit:]]+ | wc -l )
    if (( $rc == 0 )); then
      echo "JiraId  pattern invalid"
      return
    fi
    find . -name .git | while read n; do 
      d=$( dirname $n )
      echo $d
      ( 
        cd $d
        git log --abbrev-commit --pretty=oneline | grep $jira_id | while read id comment; do 
          date=$( git show -s --format=%ci $id | awk -e '{print $1}' )      
          lbl="[$date $id] $comment [$id]"
          echo $lbl
          git diff-tree --no-commit-id --name-only -r $id | prefix ' . '
        done        
      ) | prefix "  "
      tput cuu1; tput el;
    done
    echo 
}


#H - git_search_changes <JiraId>
#H   Search the git log a comment pattern
git_search_changes() {
    if [[ "$1" = "-v" ]]; then 
      verbose=true
      shift
    else
      verbose=false
    fi
    pattern=$1
    find . -name .git | while read n; do 
      d=$( dirname $n )
      echo $d
      ( 
        cd $d
        git log --abbrev-commit --pretty=oneline | egrep "$pattern" | while read id comment; do 
          date=$( git show -s --format=%ci $id | awk -e '{print $1}' )      
          lbl="[$date $id] $comment [$id]"
          echo $lbl
          git diff-tree --no-commit-id --name-only -r $id | prefix ' . '
          if [[ "$verbose" = "true" ]]; then
            git diff --color=always -r $id | prefix ' . ' 
          fi
        done        
      ) | prefix "  "
      tput cuu1; tput el;
    done
    echo 
}


#H - git_changes [-i] [-v]
#H   Search the local changes
#H     -i print mvn_idd
#H     -v print directory not update
git_changes()
{
  if [[ "$1" = "-v" ]]; then
    verbose="true"
  else 
    verbose="false"
  fi
  find . -name .git | while read n; do 
  (         
    cd $( dirname $n )
    cur=$( git rev-parse --abbrev-ref HEAD )
    if (( $? != 0 )); then
      echo $n
    fi
    file_changed=$( git diff $cur --name-only | wc -l )
    if (( $file_changed != 0 )); then
        echo "$( dirname $n ) [$(mvn_id | awk '{ print $2 }' )] [${cur}] : $file_changed files modified"
        git diff $cur --name-only | prefix ' . '
    else 
      if [[ "$verbose" = "true" ]]; then
        echo "$( dirname $n ) [${cur}] : Clean"
      fi
    fi     
  )
  done
}


#H - git_switch_branch
#H   Switch branch of all repository
git_switch_branch()
{
  branch=$1
  if [[ "$branch" = "" ]]; then
    echo "swtich_branch required the branch"
    return 1
  fi
    echo "Switching to branch $branch"
    find . -name .git | while read n; do 
      (         
        cd $( dirname $n )
        cur=$( git rev-parse --abbrev-ref HEAD )
        if [[ "$cur" != "$branch" ]]; then
          file_changed=$( git diff --name-only | wc -l )
          if (( $file_changed == 0 )); then
            echo "$( dirname $n ) [${cur}] -> [$branch]"
          else
            echo "$( dirname $n ) [${cur}] -> [$branch] : $file_changed files modified"
          fi
        fi        
      )
    done
    echo "[Enter] to confirm"
    wait_continue
    find . -name .git | while read n; do 
      (                 
        cd $( dirname $n )
        cur=$( git rev-parse --abbrev-ref HEAD )
        if [[ "$cur" != "$branch" ]]; then
          echo "Switching $( dirname $n ) from [${cur}] -> [$branch]"
          git checkout $branch 2>&1 | prefix "    "
          rc=${PIPESTATUS[0]}
          if (( $rc != 0 )); then
            echo "Checkout failed on $( dirname $n )"
          fi
        fi
      )
    done
}


#H - git_mirror origin dest
#H   Mirror the git repository from <origin> to <dest>
git_mirror()
{
    origin=$1
    dest=$2
    if [[ "$origin" = "" ]]; then
        echo "[Check] Missing origin"
        return 1
    fi
    if [[ "$dest" = "" ]]; then
        echo "[Check] Missing dest"
        return 1
    fi
    name_org=$( basename $origin)
    name_dst=$( basename $dest)
    dir_org=${name_org%.git}
    dir_dst=${name_dst%.git}
    echo "[Chk] Mirror $name_org -> $name_dst"
    echo "      From $origin"
    echo "      to   $dest"
    echo "[Org] Cloning"
    git clone $origin 2>&1 | prefix "     "
    rc=${PIPESTATUS[0]}
    if [[ "$rc" != "0" ]]; then
      echo "      [Error] Clone failed"
      return 1
    fi  
    echo "[Org] Checking if archived"
    ( cd $dir_org; git push ; return $? ) 2>&1 | prefix "     "
    rc=${PIPESTATUS[0]}
    if [[ "$rc" = "0" ]]; then
      echo "[Chk] Repository is not archived"
      echo -n "[Continue ?] " 
      wait_continue
    else
      echo "[Chk] Repository is archived"
    fi
    default_branch=$( cd $dir_org; git branch -r | grep HEAD | cut -f 2 -d '>' | xargs -L 1 basename )
    if [[ "$default_branch" = "" ]]; then
      default_branch=$( cd $dir_org; git branch -r | grep -v HEAD | xargs -L 1 basename )
    fi
    branches=$( cd $dir_org;  git branch -ar | grep -v HEAD | xargs -L 1 basename )
    echo "[Chk] branches " ${branches}
    echo "[Chk] Default ${default_branch}"
    
    mv $dir_org $dir_org.org
    echo "[Dst] Cloning"
    git clone $dest 2>&1 | prefix "      "
    rc=${PIPESTATUS[0]}
    if [[ "$rc" != "0" ]]; then
      echo "      [Error] Clone failed"
      return 1
    fi  
    mv $dir_dst $dir_dst.dst
    all_ok=true
    ( cd $dir_dst.dst; git log -1 2>&1 ; exit $? ) > /dev/null
    if [[ "$?" = "0" ]]; then
      dst_is_empty="False"
      echo "[Dst] Repository is not empty"
    else
      echo "[Dst] Repository is empty"
      dst_is_empty="True"
    fi
    
    if [[ "$dst_is_empty" = "False" ]]; then
        echo "[Chk] Checking for diff"
        for branch in $branches; do
          ( cd $dir_org.org; git checkout $branch ) >/dev/null 2>&1 
          org_commit_id=$( cd $dir_org.org; git rev-parse HEAD )
          ( cd $dir_dst.dst; git checkout $branch ) >/dev/null 2>&1
          dst_commit_id=$( cd $dir_dst.dst; git rev-parse HEAD )
          if [[ "$org_commit_id" = "$dst_commit_id" ]]; then
            echo "[Chk] Branch $branch uptodate"
          else
            echo "[Chk] Branch $branch NOT uptodate"
            echo "      [Org] $org_commit_id"
            echo "      [Dst] $dst_commit_id"
            ( cd $dir_org.org; git log -2 --pretty=format:"%h - %ad -  %s" --date=format:%Y%m%d-%H%M ) | prefix "  [org][log]"
            ( cd $dir_dst.dst; git log -2 --pretty=format:"%h - %ad -  %s" --date=format:%Y%m%d-%H%M ) | prefix "  [dst][log]"        
            all_ok=false
          fi
        done
    else 
      all_ok=false
    fi
    if [[ "$all_ok" = "true" ]]; then
      echo "[Chk] Mirror already uptodate, nothing to do"
      return 0
    else
      echo "[Continue ?] " 
      wait_continue
      rm -rf $dir_org.org
      rm -rf $dir_dst.dst
      git clone --mirror $origin
      ( cd $name_org; git push --mirror $dest; )
      rm -rf $name
    fi    
}

#H - git_move origin dest
#H   Switch remote origin from <origin> to <dest>
git_move()
{
  origin=$1
  dest=$2
  if [[ "$origin" = "" ]]; then
    echo "Missing origin"
    return 1
  fi
   if [[ "$dest" = "" ]]; then
    echo "Missing dest"
    return 1
  fi
  echo "Moving $origin to $dest"
  (
      name=$( basename $origin )
      dir=${name%.git}
      echo "Name: $name Dir: $dir"
      path=$( find . -name .git | grep ${dir}/.git )
      if [[ "$path" == "" ]]; then
        echo "Project $name[$dir] not found"
        return 1
      fi
      cd $path/..
      url=$( git config --get remote.origin.url )
      if [[ "$url" == "$dest" ]]; then
        echo "Project $name already moved"
        return 1
      fi
      if [[ "$url" != "$origin" ]]; then
        echo "Project $name origin is $url not $origin"
        return 1        
      fi
      echo "Project $name updating origin to $dest"
      git remote rm origin
      git remote add origin $dest
      echo "Set upstream branchs"
      current_branch=$( git rev-parse --abbrev-ref HEAD )
      git branch --list --no-color  | tr -d '*' | while read b; do
        echo "Set upstream of branch $b"
        git checkout $branch
        git branch --set-upstream-to=origin/$b $b        
        git pull
        git push --set-upstream origin $b
      done
      git pull --all
      git checkout $current_branch
  )  
}


#H - git_push_all
git_push_all()
{
  find . -name .git | while read n; do 
    d=$( dirname $n )
    ( 
      cd $d;
      echo "Push all branchs on $d"
      current_branch=$( git rev-parse --abbrev-ref HEAD )
      git_list_all_branches |  while read b; do
        echo "Pull branch $b"
        git checkout $b
        git push
      done
      git checkout $current_branch
    ) 2>&1
  done
}

#H - git_list_all_branches
git_list_all_branches() 
{
    (
        git fetch --prune
        branchesToDelete=$(git branch -vv | grep ' gone]')
        echo " -> Branches to delete : " >&2
        echo "$branchesToDelete" >&2
        if [[ "$branchesToDelete" != "" ]]; then
             echo "-> Deleting local branches where origin is gone" >&2
             echo "$branchesToDelete" | awk '{print $1}' | xargs git branch -d >&2
        fi
        git branch --list --no-color  | tr -d '*' | while read b; do
            echo $b
        done
        git branch --list --no-color -r | grep -v HEAD | grep -Po "origin/\K(.*)" | while read b; do
            echo $b
        done
    ) | sort | uniq 
}

#H - git_pull_all
git_pull_all()
{
  find . -name .git | while read n; do 
    d=$( dirname $n )
    ( 
      cd $d;
      echo "Pull all branchs on $d"
      current_branch=$( git rev-parse --abbrev-ref HEAD )
      git_list_all_branches |  while read b; do
        echo "Pull branch $b"
        git checkout $b
        git pull
      done | prefix '  '
      git pull --all
      git checkout $current_branch
    ) 2>&1
  done
}


#H - git_set_upstreams
#H   Reset the remote upstream
git_set_upstreams()
{
  dest=$1
  if [[ "$dest" != "" ]]; then
    git remote rm origin
    git remote add origin $dest
  fi
  find . -name .git | while read n; do 
    d=$( dirname $n )
    echo "Set upstream branchs in $d"
    ( 
      cd $d;
      echo "Set upstream branchs"
      current_branch=$( git rev-parse --abbrev-ref HEAD )
      git branch --list --no-color  | tr -d '*' | while read b; do
        echo "Set upstream of branch $b"
        git checkout $branch
        git branch --set-upstream-to=origin/$b $b        
        git pull
        git push --set-upstream origin $b
      done
      git pull --all
      git checkout $current_branch
    ) 2>&1 | prefix "  "
  done
}


#H - git_relocate
#H   Reset the remote upstream
git_relocate()
{
  loc_file=$1
  if [[ ! -f "$loc_file" ]]; then
    echo "loc_file : $loc_file does not exists"
    return 
  fi
  find . -name .git | while read n; do 
    d=$( dirname $n )
    echo "Update upstream branchs in $d"
    ( 
      cd $d;
      id=$( mvn_id | cut -f 1 -d ' ') 
      git_url=$( cat $loc_file | grep "$id$(printf '\t')" | cut -f 4 -d $'\t' )
      if [[ "${git_url}" != "" ]]; then
        git_set_upstreams "${git_url}"
      else
        echo "${id} not found in $loc_file"
        wait_continue
      fi
    ) 2>&1 | prefix "  "
  done
}

# Python commands
#H 
#H - gogs-create-repository.py [-h] [-u URL] [-t TOKEN] -o ORGANIZATION -n NAME -d DESCRIPTION
#H   Create a gogs repository
#H - gitlab-archive-repository.py [-h] [-u URL] [-t TOKEN] -g GIT [-A [ARCHIVE]] [-U [UNARCHIVE]]
#H   Archive or Unarchive a gitlab project
#H - gitlab-list.py [-h] [-u URL] [-t TOKEN] [-g GROUP] [-f FORMAT]
#H   list all gitlab projects
#H - gogs-list.py [-h] [-u URL] [-t TOKEN] [-o ORGANIZATION] [-n NAME] [-f FORMAT]
#H   list all gogs projects
#H - git-log-compact
#H   compact git log --oneline alternative with dates, times and initials

#H - git_merge_remote_repository_allowing_unrelated_histories
#H   Usage: <script_name> <subfolder_to_create> <git_repository_url>
#H   This script is here to help you merging a remote branch into the current folder.
#H   The <subfolder_to_create> shall create the folder and move the files from the remote branch in it.
#H   This script takes only the branches master and develop into account
git_merge_remote_repository_allowing_unrelated_histories()
{
    declare -a branches=( "master" "develop" )

    subfolder_or_remote_name_who_cares=$1
    git_repository_url=$2
    the_branch=$3

    if [[ "$subfolder_or_remote_name_who_cares" = "" ]]; then
        echo "Missing subfolder_to_create"
        return 1
    fi
    if [[ "$git_repository_url" = "" ]]; then
        echo "Missing git_repository_url"
        return 1
    fi

    echo "Adding the remote git repository"
    git remote add $subfolder_or_remote_name_who_cares $git_repository_url
    echo "Fetching the remote git repository"
    git fetch $subfolder_or_remote_name_who_cares

    if [[ "$the_branch" = "" ]]
    then
        for branch in ${branches[@]}
        do
            git_do_merge_and_remove_branch $subfolder_or_remote_name_who_cares $branch
        done
    else
        git_do_merge_and_remove_branch $subfolder_or_remote_name_who_cares $the_branch
    fi

    echo "Unlinking the remote git repository"
    git remote remove $subfolder_or_remote_name_who_cares
}

git_prepare_merge() {
    subfolder_or_remote_name_who_cares=$1
    git_repository_url=$2

    if [[ "$subfolder_or_remote_name_who_cares" = "" ]]; then
        echo "Missing subfolder_to_create"
        return 1
    fi
    if [[ "$git_repository_url" = "" ]]; then
        echo "Missing git_repository_url"
        return 1
    fi

    echo "Adding the remote git repository"
    git remote add $subfolder_or_remote_name_who_cares $git_repository_url
    echo "Fetching the remote git repository"
    git fetch $subfolder_or_remote_name_who_cares
}

git_do_merge() {

    subfolder_or_remote_name_who_cares=$1
    branch=$2

    if [[ "$subfolder_or_remote_name_who_cares" = "" ]]; then
        echo "Missing subfolder_to_create"
        return 1
    fi
    if [[ "$branch" = "" ]]; then
        echo "Missing branch"
        return 1
    fi

    echo "Checking out the $branch branch"
    git checkout $subfolder_or_remote_name_who_cares/$branch
    git checkout -b $subfolder_or_remote_name_who_cares/$branch
    echo "Creating the target folder $subfolder_or_remote_name_who_cares"
    mkdir $subfolder_or_remote_name_who_cares
    echo "Moving the files to $subfolder_or_remote_name_who_cares"
    for file in `ls -a`
    do

        if [[ "$file" = "pom.xml" || "$file" = "src" || "$file" = *"$subfolder_or_remote_name_who_cares"* ]]
        then
#            echo "OK: $file"
            git mv $file $subfolder_or_remote_name_who_cares/
        elif [[ "$file" != ".git" && "$file" != "." && "$file" != ".." ]]
        then
#            echo "NOK: $file"
            git rm $file
        fi
    done
    echo "Committing the changes"
    git commit -m "moving $subfolder_or_remote_name_who_cares/$branch"
    git checkout $branch
    git merge --allow-unrelated-histories $subfolder_or_remote_name_who_cares/$branch
}



git_do_merge_and_remove_branch() {

    git_do_merge $1 $2
    subfolder_or_remote_name_who_cares=$1
    branch=$2
    echo "Removing local branch $subfolder_or_remote_name_who_cares/$branch"
    git branch -D $subfolder_or_remote_name_who_cares/$branch

}

#H - git_merge_remote_repository_and_fuck_the_unrelated_histories
#H   Usage: <script_name> <subfolder_to_create> <git_repository_url>
#H   This script is here to help you merging a remote branch into the current folder.
#H   The <subfolder_to_create> shall create the folder and move the files from the remote branch in it.
#H   This script takes only the branches master and develop into account
git_merge_remote_repository_and_fuck_the_unrelated_histories() {

    declare -a branches=( "master" "develop" )

    subfolder_or_remote_name_who_cares=$1
    git_repository_url=$2
    the_branch=$3

    here=`pwd`

    working_dir=$here/../workingdir/$subfolder_or_remote_name_who_cares

    if [[ "$subfolder_or_remote_name_who_cares" = "" ]]; then
        echo "Missing subfolder_to_create"
        return 1
    fi
    if [[ "$git_repository_url" = "" ]]; then
        echo "Missing git_repository_url"
           return 1
    fi

    mkdir -p
    git clone $git_repository_url $working_dir

    for branch in ${branches[@]}
    do
        cd $working_dir
        git checkout -b $branch
        cd $here
        git checkout $branch
        if [[ "`ls | grep $subfolder_or_remote_name_who_cares`" = "" ]]
        then
            mkdir -p $subfolder_or_remote_name_who_cares
        fi
        cd $subfolder_or_remote_name_who_cares
        cp -r $working_dir/* .
        cd ..
        git add .
        git commit -m "fetching $subfolder_or_remote_name_who_cares/$branch"
    done

    cd $here
    rm -rf $working_dir
}

#H - git_verify_mandatory_files
#H   Check if mandatory files exists in current branch
git_verify_mandatory_files(){
    if [[ -e Jenkinsfile  &&  -e .gitignore ]]
    then
         echo " --> All is ok"
         return 0
    else
         echo " -->One or more of mandatory files is not present, please execute 'git_add_mandatory_files' to add them"
         return -1
    fi
}

#H - git_add_mandatory_files
#H   add mandatory files if needed
git_add_mandatory_files(){
    if [[ ! -d .git ]]; then
      echo "Not in a git repository"
      exit 1
    fi
    declare doPush='false'
    git_add_file_to_root "Jenkinsfile"
    if (( $? == 1 )); then
         git add Jenkinsfile
         git commit -m '[ESBB-1050] adding Jenkinsfile'
         doPush='true'
    fi

    git_add_update_file_to_root ".gitignore"
    if (( $? == 1 )); then
         git add .gitignore
         git commit -m '[ESBB-1050] adding .gitignore'
         doPush='true'
    fi
    git_add_update_file_to_root "git/hooks/commit-msg"  ".git/hooks/commit-msg"
    if (( $? == 1 )); then
         git commit -m '[ESBB-1050] adding .git/hooks/commit-msg'
    fi    
    if [[ $doPush == 'true' ]];
    then
        git push
    fi
}


#H - git_add_update_file_to_root
#H   add or update file to curent dir
#H   usage 'git_add_update_file_to_root param'
#H   where param is a filename
git_add_update_file_to_root () {
    if [ -z $1  ]
    then
        echo "parameter is missing"
        return
    fi
    declare destFileName=$1
    if [[ $2 != '' ]];
    then
        destFileName=$2
    fi
    #if file do not exist
    if ! [  -e ${destFileName} ]
    then
         echo "${destFileName} do not exist, adding it..."
         echo "using default file location : " ~/etc/
         mkdir -p $( dirname ./${destFileName} )
         cp ~/etc/$1 ${destFileName}
         echo "$1 added as ${destFileName}"
         return 1
     else
         cmp -s ~/etc/$1 ${destFileName}
         if (( $? == 1 )); then
           echo "${destFileName} found but different"
           cp ~/etc/$1 ${destFileName}
           echo "${destFileName} updated from $1"
           return 1
         else
           echo "${destFileName} found - not adding it"
         fi
         return 0
    fi
}

#H - git_add_file_to_root
#H   add file to curent dir
#H   usage 'git_add_file_to_root param'
#H   where param is a filename

git_add_file_to_root() {
    if [ -z $1  ]
    then
        echo "parameter is missing"
        return
    fi
    declare destFileName=$1
    if [[ $2 != '' ]];
    then
        destFileName=$2
    fi
    #if file do not exist
    if ! [  -e ${destFileName} ]
    then
         echo "${destFileName} do not exist, adding it..."
         echo "using default file location : " ~/etc/
         mkdir -p $( dirname ./${destFileName} )
         cp ~/etc/$1 ${destFileName}
         echo "$1 added as ${destFileName}"
         return 1
     else
         echo "${destFileName} found - not adding it"
         return 0
    fi
}

#git_current_branch
git_current_branch() {
    git rev-parse --abbrev-ref HEAD
    # cd $( locate_git_root ); cat .git/HEAD | cut -f 2 -d : | grep -Po "refs/heads/\K(.*)"
}

#git_checkout_release_branch
git_checkout_release_branch ()
{
    git fetch --all
    release_branches_count=$( git branch -r | grep release | wc -l )
    release_branches=$( git branch -r | grep release | grep -Po 'origin/\K(.*)' | tr -d '*' )
    echo $release_branches
    if (( $release_branches_count == 0 )); then
      echo "No release branch found"
    else
        if (( $release_branches_count == 1 )); then
          git checkout ${release_branches}
        else
          echo "Multiple release branch found " ${release_branches}
        fi
    fi    
}

#git_checkout_release_branch
git_print_release_branch ()
{
    git branch | grep release | tr -d '*'
}


#git_print_all_release_branch
git_print_all_release_branch ()
{
    git_all branch | grep release  | tr -d '*' | xargs dirname  > /tmp/$$.lst
    cat /tmp/$$.lst | sort | uniq | while read n; do
      echo "$n : $( cat /tmp/$$.lst | xargs -0 echo -n  | while read n; do echo @$n@; done | grep -F "@$n@" | wc -l )"
    done
}

locate_git_root() {
  locate_parent_file .git
}