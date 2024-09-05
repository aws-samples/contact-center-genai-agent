#!/bin/bash

##############################################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
##############################################################################################

rm -f ./import-connect-contact-flow.zip

pushd import-connect-contact-flow
zip -r ../import-connect-contact-flow.zip *
popd

if [ ! -d '../../dist' ]
then mkdir ../../dist
fi

if [ ! -d '../../dist/connect' ]
then mkdir ../../dist/connect
fi

mv ./import-connect-contact-flow.zip ../../dist/connect

echo "####################################################"
echo "Created dist/connect/import-connect-contact-flow.zip"
echo "####################################################"
