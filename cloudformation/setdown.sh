#!/bin/bash
aws s3 rb s3://subtitle.media.${USERNAME}.aws.com --force
aws s3 rb s3://subtitle.static.${USERNAME}.aws.com --force  
