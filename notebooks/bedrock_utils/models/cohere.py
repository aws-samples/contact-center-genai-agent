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

"""CohereCommandModel"""

import json
import logging
import time
from boto3 import client
from bedrock_utils.models.bedrock_model import BedrockModel

logger = logging.getLogger()
logger.setLevel(logging.INFO)

RESPONSE_MIME_TYPE = 'application/json'
INPUT_MIME_TYPE = 'application/json'

class CohereCommandModel(BedrockModel):
    COHERE_COMMAND = 'cohere.command-text-v14'
    COHERE_COMMAND_LIGHT = 'cohere.command-light-text-v14'
    COHERE_COMMAND_R = 'cohere.command-r-v1:0'
    COHERE_COMMAND_R_PLUS = 'cohere.command-r-plus-v1:0'
    MODEL_NAMES = {
        COHERE_COMMAND: 'Cohere Command',
        COHERE_COMMAND_LIGHT: 'Cohere Command Light',
        COHERE_COMMAND_R: 'Cohere Command R',
        COHERE_COMMAND_R_PLUS: 'Cohere Command R+'
    }
    
    def __init__(
        self,
        bedrock_client: client,
        model_id: str,
        instance_name: str = None,
        # defaults based on Bedrock Playground settings as of NOVEMBER, 2023
        temperature: float = 0.0,
        top_p: float = 0.99,
        top_k: int = 200,
        max_tokens: int = 300,
        stop_sequences: list = [],
        return_likelihoods: str = "NONE"
    ) -> None:
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.max_tokens = max_tokens
        self.stop_sequences = stop_sequences
        self.return_likelihoods = return_likelihoods
        super().__init__(bedrock_client, model_id, instance_name)
        
    def invoke(self,
        prompt: str,
        temperature: float = None,
        top_p: float = None,
        top_k: int = None,
        max_tokens: int = None,
        stop_sequences: list = None,
        return_likelihoods: str = None
    ) -> dict:
        
        if self.model_id in [self.COHERE_COMMAND, self.COHERE_COMMAND_LIGHT]:
            prompt_data = {
                "prompt": prompt,
                "temperature": temperature if temperature is not None else self.temperature,
                "p": top_p if top_p is not None else self.top_p,
                "k": top_k if top_k is not None else self.top_k,
                "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
                "stop_sequences": stop_sequences if stop_sequences is not None else self.stop_sequences,
                "return_likelihoods": return_likelihoods if return_likelihoods is not None else self.return_likelihoods
            }
        else:
            prompt_data = {
                "message": prompt,
                "temperature": temperature if temperature is not None else self.temperature,
                "p": top_p if top_p is not None else self.top_p,
                "k": top_k if top_k is not None else self.top_k,
                "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
                "stop_sequences": stop_sequences if stop_sequences is not None else self.stop_sequences
            }

        response = self.invoke_bedrock_model(prompt_data, INPUT_MIME_TYPE, RESPONSE_MIME_TYPE)  

        if self.model_id in [self.COHERE_COMMAND, self.COHERE_COMMAND_LIGHT]:
            response['prediction'] = response['full_response']['generations'][0].get('text')
        else:
            response['prediction'] = response['full_response'].get('text')

        if not response['prediction']:
            response['error'] = 'no prediction returned'
            response['prediction'] = 'no response from LLM'
            logger.error('<<invoke>>: {}'.format(response['error']))

        if response['prediction'][:1] == '\n':
            response['prediction'] = response['prediction'][1:]
            
        logger.info('<<invoke>>: [{}] prediction = {}'.format(
            self.model_instance_name, json.dumps(response['prediction'], indent=4)))

        return response
