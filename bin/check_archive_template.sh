STORAGE=$1
#HEADER='X-Forem-User:rgslnn'
HEADER2='X-Forem-Application:esb_perf_test'

URL_DEV=http://esb-dev.forem.be/services/Documents/Archives
USER_DEV=esb_perf_test:esb_perf_test
URL_ACC=http://esb-acc.forem.be/services/Documents/Archives
USER_ACC=esb_perf_test:0nly4EAI
URL_PROD=http://esb.forem.be/services/Documents/Archives
USER_PROD=esb_perf_test:Ju5t4T35t

if [[ "$STORAGE" = "" ]]; then
  echo "Storage ( first parameter ) required"
  exit 1
fi

mkdir tmp.$$
echo "----------------------------)" >> report.txt
for f in *.rptdesign; do
  echo "$f : $( md5 -q $f )" >> report.txt
  for env in DEV ACC PROD; do
    USER=$( eval echo \$USER_$env )
    URL=$( eval echo \$URL_$env )
    ID=$( /usr/bin/curl -u $USER -XGET -s --header $HEADER2 $URL/$STORAGE?documentName=$f | xpath "/arc:documentList/arc:document/arc:documentId/arc:docNumber/text()" 2>/dev/null )
    if [[ "$ID" = "" ]]; then
     echo "Id du document $f not found in $env "
     echo "$f : $env : -" >> report.txt
    else 
      echo "Id du document $f : $ID "
      echo /usr/bin/curl -u $USER -X GET --header $HEADER2 -o tmp.$$/$f.$env $URL/$STORAGE/$ID/content
      /usr/bin/curl -u $USER -X GET --header $HEADER2 -o tmp.$$/$f.$env $URL/$STORAGE/$ID/content
      echo "$f : $env : $ID :  $( md5 -q tmp.$$/$f.$env )" >> report.txt
    fi
  done
done
rm -rf ./tmp.$$

