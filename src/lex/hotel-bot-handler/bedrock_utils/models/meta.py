# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Llama3Model"""

import json
import logging
import time
from boto3 import client
from bedrock_utils.models.bedrock_model import BedrockModel

logger = logging.getLogger()
logger.setLevel(logging.INFO)

RESPONSE_MIME_TYPE = 'application/json'
INPUT_MIME_TYPE = 'application/json'

class Llama3Model(BedrockModel):
    LLAMA3_8B_INSTRUCT = 'meta.llama3-8b-instruct-v1:0'
    LLAMA3_70B_INSTRUCT = 'meta.llama3-70b-instruct-v1:0'
    MODEL_NAMES = {
        LLAMA3_8B_INSTRUCT: 'Meta Llama 3 8B Instruct',
        LLAMA3_70B_INSTRUCT: 'Meta Llama 3 70B Instruct'
    }
    
    def __init__(
        self,
        bedrock_client: client,
        model_id: str,
        instance_name: str = None,
        # defaults based on Bedrock Playground settings as of NOVEMBER, 2023
        temperature: float = 0.0,
        top_p: float = 1.0,
        max_tokens: int = 300
    ) -> None:
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        super().__init__(bedrock_client, model_id, instance_name)

    def invoke(self, 
        prompt: str,
        temperature: float = None,
        top_p: float = None,
        max_tokens: int = None
    ) -> dict:
        prompt_data = {
            "prompt": prompt.strip(),
            "temperature": temperature if temperature is not None else self.temperature,
            "top_p": top_p if top_p is not None else self.top_p,
            "max_gen_len": max_tokens if max_tokens is not None else self.max_tokens
        }
        
        response = self.invoke_bedrock_model(prompt_data, INPUT_MIME_TYPE, RESPONSE_MIME_TYPE)  
        response['prediction'] = response['full_response'].get('generation')

        if not response['prediction']:
            response['error'] = 'no prediction returned'
            response['prediction'] = 'no response from LLM'
            logger.error('<<invoke>>: {}'.format(response['error']))

        if response['prediction'][:1] == '\n':
            response['prediction'] = response['prediction'][1:]
            
        logger.info('<<invoke>>: [{}] prediction = {}'.format(
            self.model_instance_name, json.dumps(response['prediction'], indent=4)))

        return response
