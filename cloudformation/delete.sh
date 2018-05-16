#!/bin/bash
STACKNAME=${1}
aws cloudformation delete-stack --stack-name ${STACKNAME}
aws cloudformation wait stack-delete-complete --stack-name ${STACKNAME}
