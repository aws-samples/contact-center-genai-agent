#!/bin/bash

##############################################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
##############################################################################################

for dir in connect hallucinations lex opensearch
do
    pushd $dir
    bash publish.sh
    popd
done


