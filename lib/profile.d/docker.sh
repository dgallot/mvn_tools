#!/usr/bin/env bash

#H 
#H Docker Tools
#H -----------
#H - docker_bash <name>
#H   Open a bash on the docker image
docker_bash () 
{ 
    name=$1;
    if [[ "$name" = "" ]]; then
        echo "docker_bash <name>";
        return;
    fi;
    id=$( docker ps -aqf "name=$name" );
    docker exec -i -t $id /bin/bash
}

#H - docker_exec <name> "<command> [with_argument_one] [and_argument_two] [...]"
#H   Executes the provided command with the related arguments (must be provided between "quotes") on the docker container
#H   having the provided name.
docker_exec () {
    name=$1;
    command=` sed -e 's/^"//' -e 's/"$//' <<<$2`;
    if [[ "$name" = "" ]]; then
        echo "docker_exec <name> \"<command>\"";
        return;
    fi;
    if [[ "$command" = "" ]]; then
        echo "docker_exec <name> \"<command>\"";
        return;
    fi
    id=$( docker ps -aqf "name=$name" );
    docker exec -ti $id $command
}

#H - docker_port_mapped <name> [port]
#H   List all port mapped by a docker instance
#H   if port is provided, it only print the mapped port
docker_port_mapped () 
{ 
    name=$1;
    port=$2;
    if [[ "$name" = "" ]]; then
        echo "docker_port_mapped <name> [port]";
        return;
    fi;
    id=$( docker ps -aqf "name=$name" );
    if [[ "$id" = "" ]]; then
        echo "No docker image named $name found";
        return;
    fi;
    if [[ "$port" = "" ]]; then
        docker ps | grep --color=auto $id | perl -lae '$,="\n";foreach(@F){/tcp,?$/&&push(@x,$_)};print(@x)' | while read map; do
            to=$( echo "$map" | sed -n -e 's/^.*:\(.*\)->.*$/\1/p' );
            from=$( echo "$map" | sed -n -e 's/^.*:.*->\(.*\)\/tcp.*$/\1/p' );
            echo "$(hostname):$to -> $name:$from";
        done;
    else
        map=$( docker ps | grep $id | perl -lae '$,="\n";foreach(@F){/tcp,?$/&&push(@x,$_)};print(@x)' | grep $port/tcp );
        if [[ "$id" = "" ]]; then
            echo "No port $port found";
            docker ps | grep --color=auto $id;
            return;
        fi;
        echo "$map" | sed -n -e 's/^.*:\(.*\)->.*$/\1/p';
    fi
}

#H Activemq Tools
#H -----------
#H - activemq_admin
#H   Open the web admin tool of activemq
docker_activemq_admin()
{
  url="http://127.0.0.1:$(  docker_port_mapped activemq 8161 )"
  echo "Opening $url"
  firefox $url
}

#H - activemq_start
#H   Start the activemq docker image
docker_activemq_start()
{
  docker run --name='activemq' -d -it --rm -e 'ACTIVEMQ_MIN_MEMORY=512' -e 'ACTIVEMQ_MAX_MEMORY=2048' -p 8161:8161 -p 61616:61616 -p 61613:61613 -P webcenter/activemq:latest
}

#H - dc_clean_relaunch <name_in_docker_compose_file>
#H   For the container having the provided <name_in_docker_compose_file>,
#H   this script will kill it, remove the container, update it and launch it
dc_clean_relaunch() {

    name=$1;

    if [[ "$name" = "" ]]; then
        echo "docker_clean_relaunch <name_in_docker_compose_file>";
        return;
    fi;

    docker-compose kill $name
    docker-compose rm -vf $name
    docker-compose pull $name
    docker-compose up -d $name
}

#H - dc_deep_clean_relaunch <name_in_docker_compose_file>
#H   For the container having the provided <name_in_docker_compose_file>,
#H   this script will kill it, remove the container, delete the content of the data folder, update it and launch it
dc_deep_clean_relaunch() {

    name=$1;

    if [[ "$name" = "" ]]; then
        echo "docker_clean_relaunch <name_in_docker_compose_file>";
        return;
    fi;

    docker-compose kill $name
    docker-compose rm -vf $name
    echo "About to delete the content of the folder ./$name/data/"
    sudo rm -rf ./$name/data/*
    docker-compose pull $name
    docker-compose up -d $name
}

dc_mount_m2_repository() {

    install=$1;
    c=$( mount | grep /usr/share/m2-repository | wc -l )
    if (( $c > 0 )); then
      echo "Volume mounted:" $( df -h |grep m2 )
      echo "deleting local repo /usr/share/m2-repository/be/*"
      sudo rm -rf /usr/share/m2-repository/be/*
      return 0;
    fi
    if [[ "$install" = "force" ]]; then
        echo "Forcing install of bindfs"
        sudo apt install bindfs
    fi;
    
    sudo rm -rf /usr/share/m2-repository
    sudo mkdir /usr/share/m2-repository
    sudo bindfs -o perms=755,map=`whoami`/root,create-as-user /home/`whoami`/.m2/repository /usr/share/m2-repository/
    echo "Volume mounted:"
    df -h |grep m2
}

#H - update_docker_compose
#H   Updates docker-compose to the latest version (currently 1.21.0)
update_docker_compose() {
    sudo curl -L https://github.com/docker/compose/releases/download/1.21.0/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
}
