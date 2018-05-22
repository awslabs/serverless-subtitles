#!/bin/bash
DIRECTORY_LIST=$(ls -d */)
for DIR in ${DIRECTORY_LIST}
do
  cd ${DIR};
  DIRNAME=$(basename $(pwd));
  zip -q -X -r index.zip *;
  aws lambda update-function-code --function-name ${DIRNAME} \
    --zip-file fileb://index.zip --query 'FunctionName' --output text;
  rm index.zip;
  cd ..;

done
