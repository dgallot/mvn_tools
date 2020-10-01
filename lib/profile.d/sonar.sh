#!/usr/bin/env bash

lib_folder="${HOME}/lib/java"
sonar_helper_version="1.2"
sonar_helper_tool="sonar-helper-${sonar_helper_version}-jar-with-dependencies.jar"

#H - sonar_update_pom
#H   updates the pom to meet the expected settings for sonar
sonar_update_pom() {
    mvn_set_parent_common
    mvn-add-template.py -f sonar.xml
}

#H - sonar_update_pom_all
#H   updates the pom to meet the expected settings for sonar for every direct sub-folders
sonar_update_pom_all() {

    for project in `ls`; do
        cd ${project}
        sonar_update_pom
        cd ..
    done

}
sonar_fetch_tool() {

    if [ ! -d ${lib_folder} ]; then
        mkdir -p ${lib_folder}
    fi

    if [ ! -f "${lib_folder}/${sonar_helper_tool}" ]; then
        file_url="http://10.6.240.212:8081/nexus/content/repositories/releases/be/voo/esb/sonar-helper/${sonar_helper_version}/${sonar_helper_tool}"
        wget ${file_url}
        mv ${sonar_helper_tool} ${lib_folder}/
    fi

}

#H - sonar_create_settings
#H   creates the sonar-project.properties file for
sonar_create_settings() {
    sonar_fetch_tool
    java -jar ${lib_folder}/${sonar_helper_tool}
}

#H - sonar_create_settings_all
#H   creates sonar-project.properties for every direct sub-folders
sonar_create_settings_all() {

    for project in `ls`; do
        cd ${project}
        sonar_create_settings
        cd ..
    done

}