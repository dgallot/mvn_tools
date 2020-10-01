#!/bin/sh

noe_copy_dev() {
  cd /Users/forem/sources/noe/10-NOE-NOEP2DEV/as
  scp -r xsldir weblogic@sundwl1202.forem.be:/opt/weblogic/12.2/user_projects/NOE_AS/appfiles
 
  cd /Users/forem/sources/noe/10-NOE-NOEP2DEV/ps
  scp -r xslt weblogic@sundwl1202.forem.be:/opt/weblogic/12.2/user_projects/NOE_PS_INT/appfiles
  
  scp  /Users/forem/sources/noe/10-NOE-NOEP2DEV/ps/build/war/noe_psint.war weblogic@sundwl1202.forem.be:/opt/weblogic/12.2/user_projects/NOE_PS_INT/noe_psint_romev3.war
  scp /Users/forem/sources/noe/10-NOE-NOEP2DEV/build/ear/wl/as.ear weblogic@sundwl1202.forem.be:/opt/weblogic/12.2/user_projects/NOE_AS/as_romev3.ear
          
  scp /Users/forem/sources/noe/10-NOE-NOEP2DEV/ear/target/NOEP2DEV-ear-27.0.1-SNAPSHOT.ear weblogic@sundwl1202.forem.be:/opt/weblogic/12.2/user_projects/NOE_AS/NOEP2DEV-ear-27.0.1-SNAPSHOT-romev3.ear
}

noe_copy_deploy() {
  version=$1
  if [[ "$version" == "" ]]; then
    echo "Version is mandatory"
    return
  fi
  ssh deploy-noe mkdir -p /opt/deployment/noe/noe_psint/$version/packages/war
  scp /Users/forem/sources/noe/10-NOE-NOEP2DEV/ps/build/war/noe_psint.war deploy-noe:/opt/deployment/noe/noe_psint/$version/packages/war
  scp -r /Users/forem/sources/noe/10-NOE-NOEP2DEV/ps/xslt deploy-noe:/opt/deployment/noe/noe_psint/$version/packages/xslt
  
  ssh deploy-noe mkdir -p /opt/deployment/noe/noe_as/$version/packages/ear
  scp /Users/forem/sources/noe/10-NOE-NOEP2DEV/build/ear/wl/as.ear deploy-noe:/opt/deployment/noe/noe_as/$version/packages/ear
  scp -r /Users/forem/sources/noe/10-NOE-NOEP2DEV/as/xsldir deploy-noe:/opt/deployment/noe/noe_as/$version/packages/xsldir
}


noe_copy_stylesheet( ) {
  file=$1.xsl
  context=$2
  (
    cd /Users/forem/sources/noe/10-NOE-NOEP2DEV/ps
    found=$( find . -name $file* | grep -v /target )
    c=$( echo "$found" | wc -l  )
    if (( $c == 0 )); then
        echo "Stylesheet $file not found"
    fi
    if (( $c == 1 )); then
        echo "$found"
    else
        if [[ "$context" == "" ]]; then
            echo "Multiple files found."
            echo "$found"
            return 1
        else
            found=$( echo "$found" | grep "$context" )
            c=$( echo "$found" | wc -l  )
            if (( $c == 1 )); then
                echo "$found"
           else
                echo "Multiple files found."
                echo "$found"
                return 1
            fi
        fi
    fi
    src_file=${found#./}
    echo "Src: $src_file"
    dst_file=$( find /weblogic/user_projects/NOE_PS_INT/ | grep $src_file )
    c=$( echo "$dst_file" | wc -l  )
    if (( $c == 0 )); then
        echo "Destination Stylesheet $src_file not found"
        return 1
    fi
    if (( $c != 1 )); then
        echo "Multiple destination Stylesheet $src_file not found"
        echo "$dst_file"
        return 1
    fi
    echo "$src_file -> $dst_file [ok] ?"
    read n
    cp $src_file $dst_file
  )
}


