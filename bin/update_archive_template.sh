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
    echo "Enter user:passi esb_perf_test:Ju5t4T35t"
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
  ID=$( /usr/bin/curl -u $USER -XGET -s --header $HEADER2 $URL/$STORAGE?documentName=$f | xpath "/arc:documentList/arc:document/arc:documentId/arc:docNumber/text()" 2>/dev/null )
  updated=false
  if [[ "$ID" != "" ]]; then
    echo "Id du document $f : $ID "
    echo "Update the document"
    echo "ENTER to continue"
    read n
    /usr/bin/curl -u $USER -X PUT --header $HEADER2 -F file=@$f $URL/$STORAGE/$ID/content -o update_result
  else 
    echo "Creating entry $f"
    echo "ENTER to continue"
    read n
    /usr/bin/curl -u $USER -X POST --header $HEADER2 -F file=@$f $URL/$STORAGE -o docid.txt
    ID=$( cat docid.txt)
    echo "Id du document $f : $ID "
    created=true
  fi
  echo $created 
  if [[ "$created" = "true" ]]; then
    echo "Fetch metadata"
    /usr/bin/curl -u $USER -X GET --header $HEADER2 -F file=@$f $URL/$STORAGE/$ID -o metadata.xml
    
    echo "Creation des meta datas"
    echo "<arc:document xmlns:arc='http://model.forem.be/archivage/v3' >" > new_metadata.xml
    xpath metadata.xml /arc:document/arc:documentId >> new_metadata.xml
    xpath metadata.xml /arc:document/arc:documentName >> new_metadata.xml
    cat default_metaData.xml >> new_metadata.xml
    echo "</arc:document>"  >> new_metadata.xml
    echo "Update metadata" 
    cat new_metadata.xml
    read n
    /usr/bin/curl -u $USER -X PUT --header $HEADER2 --header 'Content-Type: application/xml;charset=utf-8' -T new_metadata.xml $URL/$STORAGE/$ID
  fi 
done
rm -f docid.txt
rm -f new_metadata.xml
rm -f update_resul
echo "Done"

