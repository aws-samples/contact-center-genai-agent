#!/bin/bash

##############################################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
##############################################################################################

rm -f ./bedrock-boto3-lambda-layer.zip ./hotel-bot-handler.zip

pushd bedrock-boto3-lambda-layer
pip3 install --requirement ./requirements.txt --target=./python
zip -r ../bedrock-boto3-lambda-layer.zip ./python
rm -rf ./python
popd

pushd hotel-bot-handler
zip -r ../hotel-bot-handler.zip *
popd

if [ ! -d '../../dist' ]
then mkdir ../../dist
fi

if [ ! -d '../../dist/lex' ]
then mkdir ../../dist/lex
fi

mv ./bedrock-boto3-lambda-layer.zip ../../dist/lex
mv ./hotel-bot-handler.zip ../../dist/lex

echo "################################################"
echo "Created dist/lex/hotel-bot-handler.zip.zip"
echo "Created dist/lex/bedrock-boto3-lambda-layer.zip"
echo "################################################"
