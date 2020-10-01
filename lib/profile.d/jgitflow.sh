jgitflow_check_pom() {
  mvn help:effective-pom -Doutput=effectivepom.xml -q
  has_parameter=$( cat effectivepom.xml | grep -A 3 '<flowInitContext>' | grep 'release${release-suffix}' | wc -l )
   rm effectivepom.xml
  if (( $has_parameter == 0 )); then
    echo '   -----> Bad Jgitflow-flowInitContext. Please use esb-master(>=1.0.2) pom as parent of your project (preferred option) OR  run jgitflow_update_pom.'
    return -1
  fi
  echo " --> All is ok"
  return 0
}


#H - jgitflow_update_pom
jgitflow_update_pom() {
    mvn-add-template.py -f jgitflow.xml
}

#H - jgitflow_hotfix_start
jgitflow_hotfix_start() {
   jgitflow_check_pom
   if (( $? != 0 )); then
     return
   fi
   git_pull_all
   git_push_all

   majorMediorVersionPattern='[0-9]*\.[0-9]*\.'
   minorVersionPattern='[0-9]*$'

   gav=$(mvn_id | grep -o '[^/]*')
   groupId=$(echo $gav | cut -d ' ' -f 2)
   artifactId=$(echo $gav | cut -d ' ' -f 3)
   currentVersion=$(echo $gav | cut -d ' ' -f 4)
   hotfixVersion=$( echo $currentVersion | cut -f 1 -d - )
   # 10# is used to specify we are using base10 numbers
   minorVersion=10#$( echo ${hotfixVersion} | grep -o ${minorVersionPattern} )
   minorNumber=$((${minorVersion} + 1))

   hotfixVersion=$( echo ${hotfixVersion} | grep -o ${majorMediorVersionPattern} )$minorNumber

   echo "Automatic calculation of hotfix version : ${hotfixVersion}"

   mvn jgitflow:hotfix-start -DskipTests -DallowSnapshots=true -DallowUntracked=true -DreleaseVersion=${hotfixVersion}
}

#H - jgitflow_hotfix_end
jgitflow_hotfix_finish() {
   jgitflow_check_pom
   if (( $? != 0 )); then
     return
   fi
   git_pull_all
   git_push_all

   mvn jgitflow:hotfix-finish -DallowSnapshots=true
}


#H - jgitflow_feature_start
jgitflow_feature_start() {
    echo "-----Checking jgitflow configuration-----"
    jgitflow_check_pom
     if (( $? != 0 )); then
         return
    fi
    echo "-----Checking presence of mandatory files-----"
    git_verify_mandatory_files
    if (( $? != 0 )); then
         return
    fi
   # TODO check if in SNAPSHOT
   echo "-----Pulling origin to be up-to-date-----"
   git_pull_all
   echo "-----Pushing all local commit to make orgin up-to-date-----"
   git_push_all
   echo "-----start jgitflow feature-start-----"
   mvn jgitflow:feature-start -DskipTests -DallowSnapshots=true -DallowUntracked=true

}

#H - jgitflow_feature_end
jgitflow_feature_finish() {
   jgitflow_check_pom   
   if (( $? != 0 )); then
     return
   fi
   git_pull_all
   git_push_all
   mvn jgitflow:feature-finish
}

#H - jgitflow_release_start
jgitflow_release_start() {
    echo "-----Checking jgitflow configuration-----"
    jgitflow_check_pom
     if (( $? != 0 )); then
         return -1
    fi
    echo "-----Checking presence of mandatory files-----"
    git_verify_mandatory_files
    if (( $? != 0 )); then
         return -1
    fi

    if [[ $1 == "" ]]; then
     echo "First parameter must be release name ( like R3-2017 )"
     return -1
    fi
    releaseOrPcrName=$1
    git_pull_all
    if (( $? != 0 )); then
       return -1
    fi
    git_push_all
    if (( $? != 0 )); then
       return -1
    fi

    gav=$(mvn_id | grep -o '[^/]*')
    groupId=$(echo $gav | cut -d ' ' -f 2)
    artifactId=$(echo $gav | cut -d ' ' -f 3)
    currentVersion=$(echo $gav | cut -d ' ' -f 4)
    releaseVersion=$( echo $currentVersion | cut -f 1 -d - )

    pattern='\.[0-9]*\.[0-9]'
    mediorNumber=$( echo ${currentVersion} | grep -o ${pattern} | cut -d '.' -f2 )
    mediorNumber=$((${mediorNumber} + 1))
    nextDevVersion=$(echo "${currentVersion//$pattern/.${mediorNumber}.0}" )

    mvn jgitflow:release-start -Drelease-suffix=-${releaseOrPcrName} -DreleaseVersion=${releaseVersion} -DdevelopmentVersion=${nextDevVersion} -DskipTests -DallowSnapshots=true -DallowUntracked=true
    if (( $? != 0 )); then
       return -1
    fi
    git status
    echo "-----Add build&deploy jenkins pipeline file-----"
    git_add_file_to_root "Jenkinsfile-deploy" "Jenkinsfile"
    if (( $? == 1 )); then
         git add Jenkinsfile
         git commit -m 'cosmetic changes\n adding Jenkinsfile with deploy stage'
         git push
    fi

    #create jenkins job to finish release
    echo "-----Get config from template-----"
    curl -s -X GET http://jenkins.esb.tecteo.intra/job/template-release/config.xml -u ${JENKINS_USERNAME}:${JENKINS_TOKEN} -o /tmp/mylocalconfig.xml
    echo "-----Customize job config with gogsUrl and branch-----"
    repositoryUrl=$(git remote get-url origin)
    echo "--updating gogs url with ${repositoryUrl}"
    sed -i "s|--URL--|${repositoryUrl}|" /tmp/mylocalconfig.xml
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    echo "--updating branch name with ${current_branch}"
    sed -i "s|--branchName--|${current_branch}|" /tmp/mylocalconfig.xml
    imageName=$(echo $artifactId | cut -f 1 -d -)
    sed -i "s|--imageName--|${imageName}|" /tmp/mylocalconfig.xml
    minorVersionPattern='[0-9]*$'
    endByXVersion=$(echo "${releaseVersion}" | sed  "s/${minorVersionPattern}/x/")
    jobName=release_${artifactId}-${releaseOrPcrName}-${endByXVersion}
    echo "-----Get a CRUMB token from jenkins-----"
    CRUMB=$(curl -s 'http://jenkins.esb.tecteo.intra/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,":",//crumb)' -u ${JENKINS_USERNAME}:${JENKINS_TOKEN})
    echo "-----Create Jenkins jobs ${jobName}-----"
    curl -s -XPOST "http://jenkins.esb.tecteo.intra/createItem?name=${jobName}" -u ${JENKINS_USERNAME}:${JENKINS_TOKEN} --data-binary @/tmp/mylocalconfig.xml -H $CRUMB -H "Content-Type:text/xml"
    echo "-----Job created-----"
    rm /tmp/mylocalconfig.xml
    echo "-----Job link-----"
    echo "http://jenkins.esb.tecteo.intra/job/${jobName}"
}

#H - jgitflow_release_start
jgitflow_express_release() {
    jgitflow_release_start "$@"
    if (( $? != 0 )); then
           return -1
    fi
    releaseJob=${jobName}
    echo "Starting ${releaseJob}"
    curl -s -XPOST "http://jenkins.esb.tecteo.intra/job/${releaseJob}/buildWithParameters" -u ${JENKINS_USERNAME}:${JENKINS_TOKEN} -H $CRUMB
    echo "See Logs ==> http://jenkins.esb.tecteo.intra/job/${releaseJob}/lastBuild/console"
}

#H - jgitflow_release_intermediate_finish
jgitflow_release_intermediate_finish() {
     echo "----- Checking jgitflow configuration -----"
     jgitflow_check_pom
     if (( $? != 0 )); then
         return -1
    fi
    echo "----- Checking presence of mandatory files -----"
    git_verify_mandatory_files
    if (( $? != 0 )); then
         return -1
    fi
    current_branch=$( git rev-parse --abbrev-ref HEAD )
    if [[ $current_branch = release* ]] || [[ $current_branch = hotfix* ]] ; then
     suffix=$( echo $current_branch | cut -f 1 -d / | grep -Po "release\K(.*)" )
     echo "----- Start intermediate maven release of release branch ${current_branch} -----"
     echo '----- Try to be up-to-date : Pulling from all branches -----'
     echo " --> Checkout develop"
     git checkout develop
     if (( $? != 0 )); then
          return -1
     fi
     echo " --> Pulling develop"
     git pull
     if (( $? != 0 )); then
          return -1
     fi
     echo " --> Checkout ${current_branch}"
     git checkout $current_branch
     if (( $? != 0 )); then
          return -1
     fi
     echo '----- Try to be up-to-date : pushing to all branches ----- '
     echo " --> Pushing --all"
     git_push_all
     if (( $? != 0 )); then
          return -1
     fi
     echo "----- check status -----"
     git status
     echo "----- Start jGitFlow -----"
     mvn jgitflow:release-finish -Drelease-suffix=${suffix} -DallowUntracked=true -DkeepBranch=true "$@"
     #Call set_property to put next snapshot on release branch
     if (( $? != 0 )); then
          return -1
     fi
     echo "----- End jGitFlow -----"
     echo " --> At this step, your release is done (artifacts deployed in Nexus & Gogs 'master' branch up-to-date )"

     echo "----- Tag the release in SCM -----"
     echo " -> Checkout ${current_branch}"
     git checkout ${current_branch}
     if (( $? != 0 )); then
          return -1
     fi
     currentVersion=$(mvn_id | grep -o '[^/]*$' )
     echo " --> Create Tag (${currentVersion})"
     git tag $currentVersion
     if (( $? != 0 )); then
          echo " --> Tag (${currentVersion}) seem to exist, not forcing it"
     else
         echo " --> Push Tag (${currentVersion}) to origin"
         git push origin $currentVersion;
         if (( $? != 0 )); then
              echo " @@@@@@@ ALERT : Tag was not pushed ! You'll need to do it manually from Master branch"
         fi
     fi
     echo "----- Update Maven Version to next SNAPSHOT on branch ${current_branch} -----"
     currentVersion=$(mvn_id | grep -o '[^/]*$' )
     minorVersionPattern='[0-9]*$'
     majorMediorVersionPattern='[0-9]*\.[0-9]*\.'
     # 10# is used to specify we are using base10 numbers
     minorVersion=10#$( echo ${currentVersion} | grep -o ${minorVersionPattern} )
     minorNumber=$((${minorVersion} + 1))
     majorMediorVersion=$( echo ${currentVersion} | grep -o ${majorMediorVersionPattern} )
     nextVersion=$(echo "${majorMediorVersion}${minorNumber}"-SNAPSHOT )
     mvn_set_version ${nextVersion}
     echo " --> Commit Maven Version"
     git commit -a -m 'cosmetic changes\n updating pom to X.Y.Z+1'
     echo " --> Push to origin"
     git push
   else
     echo " --> Current branch is not a release. Exiting..."
     return -1
   fi
}


#H - jgitflow_release_finish
jgitflow_release_finish() {

   bold=$(tput bold)
   normal=$(tput sgr0)
   current_branch=$( git rev-parse --abbrev-ref HEAD )
   echo "You are going to delete following branch : '${bold}${current_branch}'${normal}. Are you sure ?"
   echo "Any changes that was not merge in an other branch will be lost."
   read -p '(yes/no): ' response
   if [[ $response = yes ]] ; then

        if [[ $current_branch = release* ]] || [[ $current_branch = hotfix* ]] ; then
         suffix=$( echo $current_branch | cut -f 1 -d / | grep -Po "release\K(.*)" )
         echo "----- Closing release branch ${suffix} -----"
         gav=$(mvn_id | grep -o '[^/]*')
         artifactId=$(echo $gav | cut -d ' ' -f 3)
         version=$(mvn_id | grep -o '[^/]*$' )
         version=$( echo $version | cut -f 1 -d - )
         minorVersionPattern='[0-9]*$'
         endByXVersion=$(echo "${version}" | sed  "s/${minorVersionPattern}/x/")

         echo "Checking out develop"
         git checkout develop
         if (( $? != 0 )); then
              return -1
         fi
         echo " --> Delete remote branch"
         git push --delete origin $current_branch
         echo " --> Delete local branch"
         git branch -D $current_branch

         jobName="release_${artifactId}${suffix}-${endByXVersion}"
         echo "----- Deleting Jenkins job ${jobName} -----"
         echo " --> Get a CRUMB token from jenkins"
         CRUMB=$(curl -s 'http://jenkins.esb.tecteo.intra/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,":",//crumb)' -u ${JENKINS_USERNAME}:${JENKINS_TOKEN})
         curl -s -XPOST "http://jenkins.esb.tecteo.intra/job/${jobName}/doDelete" -u ${JENKINS_USERNAME}:${JENKINS_TOKEN} -H $CRUMB
         echo "  --> Job ${jobName} is deleted"
         return 0
        else
         echo "Current branch is not a release"
         return -1
        fi
    else
        echo "Aborting command..."
    fi
}

#H - jgitflow_finish_all
jgitflow_finish_all() {
  find . -name .git | while read n; do
     d=$( dirname $n )
     echo "Doing $d" 
     ( 
       cd $d
         version=$( mvn_id | cut -f 1 -d ' ' | cut -f 3 -d '/' )
         artifact=$( mvn_id | cut -f 1 -d ' ' | cut -f 2 -d '/' )
         current_branch=$( git rev-parse --abbrev-ref HEAD )
         c=$( git branch --list --no-color  | tr -d '*' | grep release | wc -l )
         if (( $c == 0 )); then         
            echo "[${artifact}/$version ${current_branch}] : no release branch found  "
            continue
         fi
         if (( $c > 1 )); then         
            echo "[${artifact}/$version ${current_branch}] : multiple release branch found  !!! "
            wait_continue
         fi
         release_branch=$( git branch --list --no-color  | tr -d '*' | grep release )         
         if [[ "$release_branch" != "$current_branch" ]]; then 
           echo "[${artifact}/$version ${current_branch}] : Checkout release branch ${release_branch}"         
           git checkout $release_branch         
         fi
         version=$( mvn_id | cut -f 1 -d ' ' | cut -f 3 -d '/' )
         artifact=$( mvn_id | cut -f 1 -d ' ' | cut -f 2 -d '/' )
         current_branch=$( git rev-parse --abbrev-ref HEAD )

         if [[ $current_branch = release* ]] || [[ $current_branch = hotfix* ]] ||  [[ $current_branch = feature* ]] ; then
           echo "[${artifact}/$version ${current_branch}] : jgitflow_finish "
           wait_continue
           jgitflow_finish | prefix "    "       
           wait_continue
         else 
           echo "[${artifact}/$version ${current_branch}] : nothing to do "
         fi
     )
  done
}