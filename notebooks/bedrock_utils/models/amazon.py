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

"""AmazonTitanModel"""

import json
import logging
import time
from boto3 import client
from bedrock_utils.models.bedrock_model import BedrockModel

logger = logging.getLogger()
logger.setLevel(logging.INFO)

RESPONSE_MIME_TYPE = 'application/json'
INPUT_MIME_TYPE = 'application/json'

class AmazonTitanModel(BedrockModel):
    TITAN_TEXT_LITE = 'amazon.titan-text-lite-v1'
    TITAN_TEXT_EXPRESS = 'amazon.titan-text-express-v1'
    TITAN_TEXT_AGILE = 'amazon.titan-text-agile-v1'
    TITAN_TEXT_PREMIER = 'amazon.titan-text-premier-v1:0'    
    MODEL_NAMES = {
        TITAN_TEXT_LITE: 'Amazon Titan Text G1 - Lite',
        TITAN_TEXT_EXPRESS: 'Amazon Titan Text G1 - Express',
        TITAN_TEXT_AGILE: 'Amazon Titan Text G1 - Agile',
        TITAN_TEXT_PREMIER: 'Amazon Titan Text Premier'
    }
    
    def __init__(
        self,
        bedrock_client: client,
        model_id: str,
        instance_name: str = None,
        temperature: float = 0.0,
        top_p: float = 1.0,
        max_tokens: int = 300,
        stop_sequences: list = []
    ) -> None:
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.stop_sequences = stop_sequences        
        super().__init__(bedrock_client, model_id, instance_name)
     
    def invoke(self,
        prompt: str,
        temperature: float = None,
        top_p: float = None,
        max_tokens: int = None,
        stop_sequences: list = None
    ) -> dict:
        prompt_data = {
            "inputText": prompt,
            "textGenerationConfig": {
                "temperature": temperature if temperature is not None else self.temperature,
                "topP": top_p if top_p is not None else self.top_p,
                "maxTokenCount": max_tokens if max_tokens is not None else self.max_tokens,
                "stopSequences": stop_sequences if stop_sequences is not None else self.stop_sequences
            }
        }
        
        response = self.invoke_bedrock_model(prompt_data, INPUT_MIME_TYPE, RESPONSE_MIME_TYPE)        
        response['prediction'] = response['full_response']['results'][0].get('outputText')

        if not response['prediction']:
            response['error'] = 'no prediction returned'
            response['prediction'] = 'no response from LLM'
            logger.error('<<invoke>>: {}'.format(response['error']))

        if response['prediction'][:1] == '\n':
            response['prediction'] = response['prediction'][1:]
            
        logger.info('<<invoke>>: [{}] prediction = {}'.format(
            self.model_instance_name, json.dumps(response['prediction'], indent=4)))

        return response
