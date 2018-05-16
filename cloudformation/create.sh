#!/bin/bash
STACKNAME=${1}
TEMPLATEBODY=$(cat templates/${1}.yml)

if [[ "${1}" == "security" ]];
then
  PARAMETERS="--parameters ParameterKey=Username,ParameterValue=${USERNAME}"
fi;

aws cloudformation validate-template --template-body "${TEMPLATEBODY}"
aws cloudformation create-stack --stack-name ${STACKNAME} --template-body "${TEMPLATEBODY}" --capabilities CAPABILITY_NAMED_IAM  ${PARAMETERS}
aws cloudformation wait stack-create-complete --stack-name ${STACKNAME}
