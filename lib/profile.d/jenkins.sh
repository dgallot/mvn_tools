#!/usr/bin/env bash

check_containers() {

    path_to_be=$1

    if [[ ${path_to_be} == "" ]]; then
        echo "No path defined"
        exit 1
    fi

    cd ${path_to_be}

    active_containers=`docker-compose ps | grep Up | awk -e '{print $1}' | wc -l`

    if [[ ${active_containers} -lt 3 ]]; then
        docker-compose pull
        docker-compose up -d
    fi
}

project="esb-docker"

pipeline_update_compose() {

    if [ ! -d ${project} ]; then
        git clone http://gogs.esb.tecteo.intra/esb/esb-docker.git
    else
        cd ${project}
        git pull --all
    fi

}

pipeline_update_and_restart_container() {

    container=$1
    environment=$2

    if [[ ${container} == "" ]]; then
        echo "Container name is missing ."
        exit 1
    fi

    if [[ ${environment} == "" ]]; then
        echo "Environment is missing ."
        exit 1
    fi

    docker login --username docker --password yolo esb-registry:5000

    cd ${project}/environments/${environment}

    check_containers `pwd`

    docker-compose stop ${container}
    docker-compose pull ${container}
    docker-compose up -d ${container}

}

project_git_urls() {

    for project in `ls`; do
        if [ -d ${project} ]; then
            git_url=`grep url ${project}/.git/config | awk '{print $3}'`
            echo "${project} :: ${git_url}"
        fi
    done

}