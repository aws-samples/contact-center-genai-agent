#!/bin/bash

##############################################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
##############################################################################################

rm -f ./opensearchpy-layer.zip ./custom-resource-lambda.zip

pushd opensearchpy-layer
pip3 install --requirement ./requirements.txt --target=./python
zip -r ../opensearchpy-layer.zip ./python
rm -rf ./python
popd

pushd custom-resource-lambda
zip -r ../custom-resource-lambda.zip *
popd

if [ ! -d '../../dist' ]
then mkdir ../../dist
fi

if [ ! -d '../../dist/opensearch' ]
then mkdir ../../dist/opensearch
fi

mv ./opensearchpy-layer.zip ../../dist/opensearch
mv ./custom-resource-lambda.zip ../../dist/opensearch


echo "#######################################################"
echo "Created dist/opensearch/custom-resource-lambda.zip.zip"
echo "Created dist/opensearch/opensearchpy-layer.zip"
echo "#######################################################"
