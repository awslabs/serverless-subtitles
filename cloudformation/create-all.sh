#!/bin/bash
export USERNAME=${USERNAME}
./create.sh security
./create.sh compute
./create.sh database
./create.sh storage
./update.sh storage-permissions storage
./create.sh storage-static
./create.sh stepfunctions
./create.sh apps
./setup.sh
cd ../lambda
./publish-all.sh
AWSWEBSITE=$(aws cloudformation describe-stacks --stack-name storage-static --query 'Stacks[0].Outputs[?ExportName==`SUBS3StaticWebsite`].OutputValue' --output text)
echo "Demo has been deployed and the endpoint is : ${AWSWEBSITE}"
open ${AWSWEBSITE}
