#!/bin/bash
STACKNAME=${1}
if [[ ! -z "${2}" ]];
then
  STACKNAME=${2};
fi;

TEMPLATEBODY=$(cat templates/${1}.yml)

if [[ "${1}" == "security" ]];
then
  PARAMETERS="--parameters ParameterKey=Username,ParameterValue=${USERNAME}"
fi;

aws cloudformation validate-template --template-body "${TEMPLATEBODY}"
aws cloudformation update-stack --stack-name ${STACKNAME} --template-body "${TEMPLATEBODY}" --capabilities CAPABILITY_NAMED_IAM ${PARAMETERS}
aws cloudformation wait stack-update-complete --stack-name ${STACKNAME}
