#!/usr/bin/env bash

#H 
#H Karaf Tools
#H -----------
#H - karaf2 [instance]
#H   run the karaf of the instance
karaf2() 
{
  if [[ "$1" = "" ]]; then
    $KRF2/bin/karaf
  else
    instance=$1
    shift
    if [[ -d $KRF2/instances/$instance ]]; then
      $KRF2/instances/$instance/bin/karaf $*
    else
      echo "Instance $instance does not exist"
    fi
  fi 
}

#H - karaf4 [instance]
#H   run the karaf of the instance
karaf4()
{
  if [[ "$1" = "" ]]; then
    $KRF4/bin/karaf
  else
    instance=$1
    shift
    if [[ -d $KRF2/instances/$instance ]]; then
      $KRF4/instances/$instance/bin/karaf $*
    else
      echo "Instance $instance does not exist"
    fi
  fi
}

#H - karaf2_cd [[instance] path]
#H   cd to the karaf instance
karaf2_cd() 
{
  if (( $# == 1 )); then
    cd $KRF2/$1
  else
    if [[ -d $KRF2/instances/$1 ]]; then
      cd $KRF2/instances/$1/$2
    else
      echo "Instance $1 does not exist"
    fi
  fi 
}

#H - karaf4_cd [[instance] path]
#H   cd to the karaf instance
karaf4_cd()
{
  if (( $# == 1 )); then
    cd $KRF4/$1
  else
    if [[ -d $KRF4/instances/$1 ]]; then
      cd $KRF4/instances/$1/$2
    else
      echo "Instance $1 does not exist"
    fi
  fi
}

#H - karaf_ps
#H   Print all current karaf process for both karaf2 and karaf4
karaf_ps() {
  printf "%-12s %-10s %-7s %s : %s\n" name [pid] [ssh] [rmiRegistryPort/rmiServerPort] [httpPort] home
  ps -fu $( whoami ) | grep org.apache.karaf.main.Main | egrep -v 'grep .* org.apache.karaf.main.Main' | awk -e ' { print $2 }' | while read pid; do
    instance=$( cat /proc/${pid}/cmdline | strings | grep karaf.base | grep -Po 'instances/\K(.*)' )
    if [[ "$instance" = "" ]]; then
      instance="root"
    fi
    home=$( cat /proc/${pid}/cmdline | strings | grep -Po 'karaf\.base=\K(.*)' )
    etc=$( cat /proc/${pid}/cmdline | strings | grep -Po 'karaf\.etc=\K(.*)' )

    le_fichier_de_configuration_merci_bisous="${etc}/org.ops4j.pax.web.cfg"
    if [[ -f $le_fichier_de_configuration_merci_bisous ]]
    then
        http_port=$( cat ${etc}/org.ops4j.pax.web.cfg | grep -Po 'org.osgi.service.http.port(\s*)=(\s*)\K(.*)' )
    else
        http_port=$( cat ${etc}/jetty.xml | grep  -Po '(\s*)<Property name="jetty.port" default="\K(\d*)" />' )
    fi
    ssh_port=$( cat ${etc}/org.apache.karaf.shell.cfg | grep -Po 'sshPort(\s*)=(\s*)\K(.*)' )
    rmiRegistryPort=$(  cat ${etc}/org.apache.karaf.management.cfg | grep -Po 'rmiRegistryPort(\s*)=(\s*)\K(.*)' )
    rmiServerPort=$(  cat ${etc}/org.apache.karaf.management.cfg | grep -Po 'rmiServerPort(\s*)=(\s*)\K(.*)' )
    printf "%-20s %-10s %-7s %s %s : %s\n" $instance [$pid] [$ssh_port] [$rmiRegistryPort/$rmiServerPort] [$http_port] $home
  done
}

#H - karaf2_pull_cfg [instance] config_file
#H   Copy the configuration file [config_file] from tacceptance3 (prequal) to local intance
karaf2_pull_cfg()
{
  if [[ "$1" = "" ]]; then
    KRF_ETC=$KRF2/etc
  else
    if [[ -d $KRF2/instances/$1 ]]; then
      KRF_ETC=$KRF2/instances/$1/etc
    else
      echo "Instance $1 does not exist"
      return
    fi
  fi
  echo "Will copy configuration file $2 from acceptance to $1"  
  scp prequal:/opt/karaf/2.4.3/instances/$1/etc/$2 ~/on-boarding/files/$1
  scp prequal:/opt/karaf/2.4.3/instances/$1/etc/$2 $KRF2/instances/$1/etc/;
}

#H - karaf4_pull_cfg [instance] config_file
#H   Copy the configuration file [config_file] from tacceptance3 (prequal) to local intance
karaf4_pull_cfg()
{
  if [[ "$1" = "" ]]; then
    KRF_ETC=$KRF4/etc
  else
    if [[ -d $KRF4/instances/$1 ]]; then
      KRF_ETC=$KRF4/instances/$1/etc
    else
      echo "Instance $1 does not exist"
      return
    fi
  fi
  echo "Will copy configuration file $2 from acceptance to $1"
  scp prequal:/opt/karaf/4.0.6/instances/$1/etc/$2 ~/on-boarding/files/$1
  scp prequal:/opt/karaf/4.0.6/instances/$1/etc/$2 $KRF4/instances/$1/etc/;
}


#H - karaf2_mvnrep_cfg
#H   Create the org.ops4j.pax.url.mvn.cfg file for a karaf instance
karaf2_mvnrep_cfg()
{
  if [[ "$1" = "" ]]; then
    KRF_ETC=$KRF2/etc
  else
    if [[ -d $KRF2/instances/$1 ]]; then
      KRF_ETC=$KRF2/instances/$1/etc
    else
      echo "Instance $1 does not exist"
      return
    fi
  fi
  echo "Will override the configuration file $KRF_ETC/org.ops4j.pax.url.mvn.cfg [CTRL][C] to stop"
  wait_continue
cat > $KRF_ETC/org.ops4j.pax.url.mvn.cfg <<EOF
org.ops4j.pax.url.mvn.repositories= \\
    http://10.6.240.212:8081/nexus/content/repositories/snapshots@snapshots@noreleases@id=snapshots, \\
    http://10.6.240.212:8081/nexus/content/repositories/releases@id=releases, \\
    http://10.6.240.212:8081/nexus/content/repositories/public@id=public, \\
    http://10.6.240.212:8081/nexus/content/repositories/snapshots@snapshots@noreleases@id=snapshots, \\
    http://10.6.240.212:8081/nexus/content/repositories/releases@id=releases, \\
    http://10.6.240.212:8081/nexus/content/repositories/public@id=public, \\
    http://10.6.240.212:8081/nexus/content/repositories/releases@id=releases, \\
    http://10.6.240.212:8081/nexus/content/repositories/snapshots@snapshots@noreleases@id=snapshots, \\
    http://10.6.240.212:8081/nexus/content/repositories/public@id=public, \\
    http://repo1.maven.org/maven2@id=central, \\
    http://svn.apache.org/repos/asf/servicemix/m2-repo@id=servicemix, \\
    http://repository.springsource.com/maven/bundles/release@id=springsource.release, \\
    http://repository.springsource.com/maven/bundles/external@id=springsource.external, \\
    https://oss.sonatype.org/content/repositories/releases/@id=sonatype
EOF
}

#H - karaf4_mvnrep_cfg
#H   Create the org.ops4j.pax.url.mvn.cfg file for a karaf instance
karaf4_mvnrep_cfg()
{
  if [[ "$1" = "" ]]; then
    KRF_ETC=$KRF4/etc
  else
    if [[ -d $KRF4/instances/$1 ]]; then
      KRF_ETC=$KRF4/instances/$1/etc
    else
      echo "Instance $1 does not exist"
      return
    fi
  fi
  echo "Will override the configuration file $KRF_ETC/org.ops4j.pax.url.mvn.cfg [CTRL][C] to stop"
  wait_continue
cat > $KRF_ETC/org.ops4j.pax.url.mvn.cfg <<EOF
org.ops4j.pax.url.mvn.repositories= \\
    http://10.6.240.212:8081/nexus/content/repositories/snapshots@snapshots@noreleases@id=snapshots, \\
    http://10.6.240.212:8081/nexus/content/repositories/releases@id=releases, \\
    http://10.6.240.212:8081/nexus/content/repositories/public@id=public, \\
    http://10.6.240.212:8081/nexus/content/repositories/snapshots@snapshots@noreleases@id=snapshots, \\
    http://10.6.240.212:8081/nexus/content/repositories/releases@id=releases, \\
    http://10.6.240.212:8081/nexus/content/repositories/public@id=public, \\
    http://10.6.240.212:8081/nexus/content/repositories/releases@id=releases, \\
    http://10.6.240.212:8081/nexus/content/repositories/snapshots@snapshots@noreleases@id=snapshots, \\
    http://10.6.240.212:8081/nexus/content/repositories/public@id=public, \\
    http://repo1.maven.org/maven2@id=central, \\
    http://svn.apache.org/repos/asf/servicemix/m2-repo@id=servicemix, \\
    http://repository.springsource.com/maven/bundles/release@id=springsource.release, \\
    http://repository.springsource.com/maven/bundles/external@id=springsource.external, \\
    https://oss.sonatype.org/content/repositories/releases/@id=sonatype
EOF
}

#C remote-list-features-url.py
#C remote-list-bundle.py
#C remote-expand-features.py
#C remote-camel-route-infos.py
#C remote-camel-route-dump.py


#H - karaf2_mvnrep_cfg host instances,...
#H   Dump all routes fetch from the host provided
#H   If arg2 is omitted will connect to 
remote_all_camel_route_dump()
{
  hostname=${1:-qual1}
  instances=${2:-bmx,esb,nicedevice,wfm,bss,frontoffice,options,oss,printhandling,sapconnector,terranova}
  echo "Dumpting all routes from $hostname on instances $instances"
  for i in $( echo "$instances" | tr ',' ' ' ); do
    echo "Dump route from $i@$hostname to ~/var/route.$hostname.$i"
    remote-camel-route-dump.py -H $hostname -i bss > ~/var/route.$hostname.$i    
  done
}

