
#H 
#H Maven Tools
#H -----------
#H - createvpom [dir] [dir] [dir] ...
#H   create a virtual pom on the current directory containing all sub
#H   directories or the list of specified director
mvn_create_vpom()
{

  if [[ "$1" = "-r" ]]; then
    recursive="true"
    shift
  else
    recursive="false"
  fi
  
  dir=$(basename $( pwd ) )
  
  groupid="${1:-be.voo.esb}"
  if [[ -f "pom.xml" ]]; then  
     echo "[$dir] File pom.xml already exists, please delete it"
     return
  fi
  shift
  if(( $# == 0 )); then
    modules="*"
    echo "[$dir] Creating pom.xml with groupid ${groupid} with all maven project in subdirectories"
  else
    modules="$*"
    echo "[$dir] Creating pom.xml with groupid ${groupid} with maven project : ${modules}"
  fi

  rm -f ".createvpom.has_submodule"
  for module in $modules; do
    pom_count=0
    if [[ "$recursive" = "true" ]]; then
      # do we have at least one pom in the directory 
      if [[ -d $module ]]; then
        pom_count=$( find $module -name pom.xml | wc -l )
      fi
    else
      if [[ -f $module/pom.xml ]]; then 
        pom_count=1
      fi
    fi
    if (( $pom_count > 0 )); then
      touch .createvpom.has_submodule
    fi
  done
  if [[ ! -f ".createvpom.has_submodule" ]]; then 
    echo "[$dir] Will not create pom.xml, no modules found"  >&2
    rm ".createvpom.has_submodule"
    return
  fi
  rm ".createvpom.has_submodule"
  
  {
  cat <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/maven-v4_0_0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <name>${dir} parent project</name>
    <groupId>be.voo.esb</groupId>
    <artifactId>${dir}</artifactId>
    <packaging>pom</packaging>
    <version>0.0.0</version> 
    <build>
    <plugins>    
    <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-deploy-plugin</artifactId>
        <version>2.7</version>
        <configuration>
            <skip>true</skip>
        </configuration>
    </plugin>
    </plugins>
    </build>
    <modules>
EOF
    for module in $modules; do
      if [[ "$recursive" = "true" ]]; then
        if [[ -d $module ]]; then
          if [[ ! -f $module/pom.xml ]]; then
            (
                cd $module
                mvn_create_vpom -r 2>&1 | prefix "--" >&2 
            )
          fi
        fi
      fi
      if [[ -f $module/pom.xml ]]; then 
        echo "  [$dir] Adding $module" >&2
        echo "        <module>$module</module>"
      else
        if [[ -e $module ]]; then
          if [[ -d $module ]]; then
            echo "  [$dir] Skipping $module, not a maven project" >&2
          fi
        else
          echo "  [$dir] Skipping $module, does not exist" >&2
        fi
      fi
    done
  cat <<EOF
    </modules>
</project>  
EOF
  } > pom.xml
}

#H - mvn_remove_vpom
#H   create a virtual pom created by mvn_createv_pom
mvn_remove_vpom()
{
  mvn_ids -v | grep 'be.voo.esb/' | grep 0.0.0 | while read n i; do echo $n; rm $n/pom.xml; done
}

#H - mvn_build_all
#H   builds all the projects of the current folder
mvn_build_all()
{
	for project in `ls`
	do
		cd $project
		mvn clean install -DskipTests
		cd ..
	done
}

#H - mvn_build_all_with_tests
#H   builds all the projects of the current folder
mvn_build_all_with_tests()
{
	for project in `ls`
	do
		cd $project
		mvn clean install
		cd ..
	done
}

#H 
#H Mr Tools
#H -----------
#H - mr_register_all
#H   Register all git project in mr

mr_register_all()
{
  find . -name .git | while read n; do 
    d=$( dirname $n )
    echo $d
    ( cd $d; mr register . ) | prefix "  "
  done
}

#H 
#H Mvn Tools
#H -----------
#H - mvn_id
#H   Print the current maven id
mvn_id()
{
    mvn-id.py "$@"
}
#H - mvn_ids
#H   find all project and print there maven id
mvn_ids()
{
    mvn-ids.py "$@"
}

#H - mvn_cd
#H   change the currentl directory to the specified id
mvn_cd()
{
    id="$1"
    if [[ "$id" = "" ]]; then
      echo "Require <id> parameter" >&2
      return 1
    fi
    founds=$( mvn_find "$id" | filter_empty_comment )
    if [[ "$( echo $founds )" = "" ]]; then
      echo "No maven project not found matching $id" >&2
      return 1
    fi
    dir=$(  echo "$founds" | head -1 | awk -e '{print $1}'  )
    id=$(  echo "$founds" | head -1 | awk -e '{print $2}'  )
    echo "Changing to $dir [$id]"
    cd $dir    
}

#H - mvn_find
#H   Search a mvn_id recursivly
mvn_find()
{
    mvn-find.py "$@"
}

#H - mvn_set_version
#H   Update the pom version to the provided value
mvn_set_version(){
    mvn-set-version.py "$@"
}
#H - changes_vi
#H   Edit the changes file in vi
changes_vi()
{
  local project=""
  if [[ "$1" = "-p" ]]; then
    shift
    project="$1"
    shift
  fi
    changes_file=$( locate_changes_file -p "$project" . )    
    if (( $? != 0 )); then
      return 1
    fi
    echo "Editing ${changes_file}"
    vi  ${changes_file}
}


#H - mvn_set_parent_common
#H   Set the parent pom to be.voo.esb.common/esb-master/1.0.4
mvn_set_parent_common() {
    mvn-set-parent.py be.voo.esb.common/esb-master/1.0.8
}

#H - mvn_set_parent_common
#H   Set the parent pom to provided pom value
mvn_set_parent() {
    mvn-set-parent.py "$@"
}

#H - bring_back_my_repo [path]
#H   Resets the permissions on the local repository that were screwed by Karaf on Docker.
#H   If no [path] is provided, the script will use ~/.m2/repository
bring_back_my_repo() {

    repo_path="$1"
    user="`whoami`"
    if [[ "$repo_path" = "" ]]; then
        repo_path="/home/$user/.m2/repository"
    fi;

    sudo chown -R $user $repo_path
}

#H - mount_the_repo_for_docker
#H   Creates the folder /usr/share/m2-repository, clean what's inside and mount the repository of the logged user on this folder.
mount_the_repo_for_docker() {
    sudo mkdir -p /usr/share/m2-repository
    sudo rm -rf /usr/share/m2-repository/*
    sudo bindfs -o perms=755,map=`whoami`/root,create-as-user /home/`whoami`/.m2/repository /usr/share/m2-repository/
}

#H Will read all version from a feature bundle and check that all pom dependencies are in line with this version
#H   $1 : path to feature bundle
#H   $2 : filter ( SNAPSHOT )
mvn_sync_version_from_feature() {
  feature_path=$1
  shift
  filter=$1
  shift
  if [[ "$feature_path" = "" ]]; then
    echo "Usage <feature_path> <filter>"
    return
  fi
  if [[ "$filter" = "" ]]; then
    echo "Usage <feature_path> <filter>"
    return
  fi
  
  affected_bundles=$( cd $feature_path; mvn-version-tools.py -f  -q | awk '{ print $4 }' | grep $filter )
  ( cd $feature_path; mvn-version-tools.py -f  -q | awk '{ print $4 }' > /tmp/all_bundles.$$ )
  mvn-resolve.py /tmp/all_bundles.$$ > /tmp/all_sources.$$

  for bundle in $affected_bundles; do
    g=$( echo $bundle | cut -f 1 -d '/' )    
    a=$( echo $bundle | cut -f 2 -d '/' )
    v=$( echo $bundle | cut -f 3 -d '/' )
    echo "Sync ${g}/$a to version ${v}"
    mvn-version-tools.py -b "${g}/${a}" -u ${v} -s /tmp/all_sources.$$ -c ${v} 
    wait 3
  done 
}

#H Run a mvn command on all project located in a feature bundle that match a filter
#H   $1 : path to feature bundle
#H   $2 : filter ( SNAPSHOT )
#H   $3...$99 : mvn parameter
mvn_all_from_feature() {
  feature_path=$1
  shift
  filter=$1
  shift
  if [[ "$feature_path" = "" ]]; then
    echo "Usage <feature_path> <filter>"
    return
  fi
  if [[ "$filter" = "" ]]; then
    echo "Usage <feature_path> <filter>"
    return
  fi
  
  ( cd $feature_path; mvn-version-tools.py -f  -q | awk '{ print $4 }' | grep $filter ) > /tmp/affected_bundles.$$
  ( cd $feature_path; mvn_id | awk '{ print $2 }' ) >> /tmp/feature_bundle.$$  
  mvn-resolve.py -g /tmp/affected_bundles.$$ > /tmp/all_sources.$$
  mvn-resolve.py -g /tmp/feature_bundle.$$   >> /tmp/feature_source.$$
  
  cat /tmp/all_sources.$$ | awk '{ print $3 }' | sort | uniq | while read d; do 
      cd $d
      pwd
      mvn "$@" | prefix "$d"
      if (( ${PIPESTATUS[0]} != 0 )); then
        wait_continue
      fi
  done    
  cat /tmp/feature_source.$$ | awk '{ print $3 }' | sort | uniq | while read d; do 
      cd $d
      pwd
      mvn "$@" | prefix "$d"
      if (( ${PIPESTATUS[0]} != 0 )); then
        wait_continue
      fi
  done      
}

#H Check all modified project, and check that the feature bundle version are synced with the version on disk
#H   $1 : path to feature bundle
#H   $2 : filter ( SNAPSHOT )
updated_files_show_check_pom_version() {
  base_dir=${1:-.}
  mvn_ids_impacted_files | awk ' { print $2 }' | sort | uniq > /tmp/updated.mvn_id.$$
  (   
    cd $base_dir
    for bundle in $( cat /tmp/updated.mvn_id.$$ ); do
        g=$( echo $bundle | cut -f 1 -d '/' )    
        a=$( echo $bundle | cut -f 2 -d '/' )
        v=$( echo $bundle | cut -f 3 -d '/' )
        printf "${IBlue}Checking that version of ${g}/${a} are all set to ${v} ${NoColor}"
        echo

        mvn-version-tools.py -b "${g}/${a}" -u ${v} -s /tmp/all_sources.$$ -c ${v}  
        wait 3
    done
  )
}



mvn_ids_impacted_files() 
{
  find . -name .git | while read n; do 
  (         
    cd $( dirname $n )    
    cur=$( git rev-parse --abbrev-ref HEAD )
    if (( $? == 0 )); then
        diff=$( git diff $cur --name-only | wc -l )
        if (( $diff != 0 )); then
            mvn_ids
        fi
    fi
  )
  done
}

mvn_ids_file_changed()
{
  find . -name .git | while read n; do 
  (         
    cd $( dirname $n )
    cur=$( git rev-parse --abbrev-ref HEAD )
    if (( $? == 0 )); then
        git diff $cur --name-only | while read n; do  
          parent_pom_location=$(locate_parent_file pom.xml $( dirname $n ) )
          echo $( cd $parent_pom_location; mvn_id | awk ' { print $2 }' ) $n 
        done
    fi
  )
  done
}