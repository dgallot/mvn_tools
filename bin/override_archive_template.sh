ENV=$1
STORAGE=$2
#HEADER='X-Forem-User:rgslnn'
HEADER2='X-Forem-Application:esb_perf_test'

case $ENV in
  DEV)
    URL=http://esb-dev.forem.be/services/Documents/Archives
    USER=esb_perf_test:esb_perf_test
    ;;
  ACC)
    URL=http://esb-acc.forem.be/services/Documents/Archives
    USER=esb_perf_test:0nly4EAI
    ;;
  PROD)
    URL=http://esb.forem.be/services/Documents/Archives
    echo "Enter user:pass"
    read USER
    ;;
  *)
   echo "Invalid env. Must be DEV/ACC/PROD"
   exit 1
esac

if [[ "$STORAGE" = "" ]]; then
  echo "Storage ( first parameter ) required"
  exit 1
fi

if [[ ! -f default_metaData.xml ]]; then
  echo "Missing default_metaData.xml"
  exit 1
fi  

echo "Updating template $STORAGE on $URL using $USER"

for f in *.rptdesign; do
  ID=$( /usr/bin/curl -u $USER -XGET -s --header $HEADER2 $URL/$STORAGE?documentName=$f | myxpath "/arc:documentList/arc:document/arc:documentId/arc:docNumber/text()" 2>/dev/null )
  IDCOUNT=$( /usr/bin/curl -u $USER -XGET -s --header $HEADER2 $URL/$STORAGE?documentName=$f | myxpath "/arc:documentList/arc:document/arc:documentId/arc:docNumber/text()" 2>/dev/null | wc -l )
  if (( "$IDCOUNT" != 1 )); then 
    echo "Multiple id found for $f $ID"
    echo /usr/bin/curl -u $USER -X DELETE --header $HEADER2 $URL/$STORAGE/$ID
    exit 1
  fi
  METADATA_FETCH=false
  if [[ "$ID" != "" ]]; then
    echo "Id du document $f : $ID "
    echo "Fetch des meta datas"
    /usr/bin/curl -u $USER -X GET --header $HEADER2 -F file=@$f $URL/$STORAGE/$ID -o metadata.xml
    METADATA_FETCHED=true
    echo "Suppression du document"
    echo "ENTER to continue"
    read n
    /usr/bin/curl -u $USER -X DELETE --header $HEADER2 $URL/$STORAGE/$ID
    ID=""
  fi 
  echo "Creating entry $f"
  echo "ENTER to continue"
  read n
 
  /usr/bin/curl -u $USER -X POST --header $HEADER2 -F file=@$f $URL/$STORAGE -o docid.txt
  ID=$( cat docid.txt)
  echo "Id du document $f : $ID "
  if [[ "$METADATA_FETCHED" = "false" ]]; then
    echo "Fetch metadata"
    /usr/bin/curl -u $USER -X GET --header $HEADER2 -F file=@$f $URL/$STORAGE/$ID -o metadata.xml
  fi
  echo "Creation des meta datas"
  echo "<arc:document xmlns:arc='http://model.forem.be/archivage/v3' >" > new_metadata.xml
  myxpath metadata.xml /arc:document/arc:documentId  >> new_metadata.xml 2>/dev/null
  myxpath metadata.xml /arc:document/arc:documentName  >> new_metadata.xml 2>/dev/null
  cat default_metaData.xml >> new_metadata.xml
  echo "</arc:document>"  >> new_metadata.xml
  echo "Update metadata" 
  /usr/bin/curl -u $USER -X PUT --header $HEADER2 --header 'Content-Type: application/xml;charset=utf-8' -T new_metadata.xml $URL/$STORAGE/$ID
  done
echo "Done"

