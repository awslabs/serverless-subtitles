#!/bin/bash
# Extract data to setup the website
AWSMEDIABUCKET=$(aws cloudformation describe-stacks --stack-name storage --query 'Stacks[0].Outputs[?ExportName==`SUBS3Media`].OutputValue' --output text);
AWSSTATICBUCKET=$(aws cloudformation describe-stacks --stack-name storage-static --query 'Stacks[0].Outputs[?ExportName==`SUBS3Static`].OutputValue' --output text);
AWSCOGNITOIDENTITYPOOLID=$(aws cloudformation describe-stack-resources --stack-name apps --query 'StackResources[?ResourceType==`AWS::Cognito::IdentityPool`].PhysicalResourceId' --output text);
echo "{\"mediaBucket\": \"${AWSMEDIABUCKET}\", \"staticBucket\":\"${AWSSTATICBUCKET}\", \"cognitoIdentityPool\":\"${AWSCOGNITOIDENTITYPOOLID}\"}" > ../s3/static/config.json

# Then Sync static bucket
aws s3 sync ../s3/static/ s3://subtitle.static.${USERNAME}.aws.com/
