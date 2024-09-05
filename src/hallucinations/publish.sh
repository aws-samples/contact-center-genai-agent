#!/bin/bash

##############################################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
##############################################################################################

rm -f ./hallucination-detection-function.zip

pushd hallucination-detection-function
zip -r ../hallucination-detection-function.zip *
popd

if [ ! -d '../../dist' ]
then mkdir ../../dist
fi

if [ ! -d '../../dist/hallucinations' ]
then mkdir ../../dist/hallucinations
fi

mv ./hallucination-detection-function.zip ../../dist/hallucinations

echo "################################################################"
echo "Created dist/hallucinations/hallucination-detection-function.zip"
echo "################################################################"

