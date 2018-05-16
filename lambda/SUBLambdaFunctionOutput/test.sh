#!/bin/bash
clear
DIRNAME=$(basename $(pwd))
$(aws lambda invoke --function-name "${DIRNAME}" --log-type Tail --query 'LogResult' --output text --payload file://./test/test.json output.txt > output.txt)
base64 -D "output.txt"
rm output.txt
