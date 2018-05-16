#!/bin/bash
export USERNAME=${USERNAME}
./setdown.sh
./delete.sh apps
./delete.sh stepfunctions
./delete.sh database
./delete.sh storage
./delete.sh storage-static
./delete.sh compute
./delete.sh security
