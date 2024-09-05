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

"""AI21LabsJurassic2Model, AI21LabsJambaModel"""

import json
import logging
import time
from boto3 import client
from bedrock_utils.models.bedrock_model import BedrockModel

logger = logging.getLogger()
logger.setLevel(logging.INFO)

RESPONSE_MIME_TYPE = 'application/json'
INPUT_MIME_TYPE = 'application/json'

class AI21LabsJurassic2Model(BedrockModel):
    JURASSIC_2_MID = 'ai21.j2-mid-v1'
    JURASSIC_2_ULTRA = 'ai21.j2-ultra-v1'
    MODEL_NAMES = {
        JURASSIC_2_MID: 'AI21 Labs Jurassic-2 Mid',
        JURASSIC_2_ULTRA: 'AI21 Labs Jurassic-2 Ultra'
    }
    
    def __init__(
        self,
        bedrock_client: client,
        model_id: str,
        instance_name: str = None,
        temperature: float = 0.0,
        top_p: float = 1.0,
        max_tokens: int = 300,
        stop_sequences: list = [],
        count_penalty: dict = {},
        presence_penalty: dict = {},
        frequency_penalty: dict = {}
    ) -> None:
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.stop_sequences = stop_sequences
        self.count_penalty = count_penalty
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        super().__init__(bedrock_client, model_id, instance_name)
        
    def invoke(self, 
        prompt: str,
        temperature: float = None,
        top_p: float = None,
        max_tokens: int = None,
        stop_sequences: list = None,
        count_penalty: dict = None,
        presence_penalty: dict = None,
        frequency_penalty: dict = None
    ) -> dict:
        prompt_data = {
            "prompt": prompt,
            "temperature": temperature if temperature is not None else self.temperature,
            "topP": top_p if top_p is not None else self.top_p,
            "maxTokens": max_tokens if max_tokens is not None else self.max_tokens,
            "stopSequences": stop_sequences if stop_sequences is not None else self.stop_sequences,
            "countPenalty": count_penalty if count_penalty is not None else self.count_penalty,
            "presencePenalty": presence_penalty if presence_penalty is not None else self.presence_penalty,
            "frequencyPenalty": frequency_penalty if frequency_penalty is not None else self.frequency_penalty
        }
        
        response = self.invoke_bedrock_model(prompt_data, INPUT_MIME_TYPE, RESPONSE_MIME_TYPE)
        response['prediction'] = response['full_response']['completions'][0]['data'].get('text')

        if not response['prediction']:
            response['error'] = 'no prediction returned'
            response['prediction'] = 'no response from LLM'
            logger.error('<<invoke>>: {}'.format(response['error']))

        if response['prediction'][:1] == '\n':
            response['prediction'] = response['prediction'][1:]

        logger.info('<<invoke>>: [{}] prediction = {}'.format(
            self.model_instance_name, json.dumps(response['prediction'], indent=4)))

        return response

class AI21LabsJambaModel(BedrockModel):
    JAMBA_INSTRUCT = 'ai21.jamba-instruct-v1:0'
    MODEL_NAMES = {
        JAMBA_INSTRUCT: 'AI21 Labs Jamba Instruct'
    }
    
    def __init__(
        self,
        bedrock_client: client,
        model_id: str,
        instance_name: str = None,
        temperature: float = 0.0,
        top_p: float = 1.0,
        max_tokens: float = 300,
        # stop_sequences: list = ['\n\nHuman:']
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
        top_k: int = None,
        max_tokens: int = None,
        stop_sequences: list = None
    ) -> dict:

        system = None
        human = None
        assistant = None
        
        if 'Assistant:' in prompt:
            prompt, assistant = prompt.split('Assistant:')
        
        if 'Human:' in prompt:
            prompt, human = prompt.split('Human:')
        
        if 'System:' in prompt:
            prompt, system = prompt.split('System:')
            
        user = human if human else prompt

        prompt_data = {
            "temperature": temperature if temperature is not None else self.temperature,
            "top_p": top_p if top_p is not None else self.top_p,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            "stop": stop_sequences if stop_sequences is not None else self.stop_sequences,
            "messages": []
        }
        if system:
            prompt_data['messages'].append({"role": "system", "content": user.strip()})
        if user:
            prompt_data['messages'].append({"role": "user", "content": user.strip()})
        if assistant:
            prompt_data['messages'].append({"role": "assistant", "content": assistant.strip()})

        response = self.invoke_bedrock_model(prompt_data, INPUT_MIME_TYPE, RESPONSE_MIME_TYPE)
        
        content = response['full_response'].get('choices',[])
        if len(content) == 0:
            response['prediction'] = None
        else:
            response['prediction'] = content[0].get('message', {}).get('content', None)

        if not response['prediction']:
            response['error'] = 'no prediction returned'
            response['prediction'] = 'no response from LLM'
            logger.error('<<invoke>>: {}'.format(response['error']))

        if response['prediction'][:1] == ' ':
            response['prediction'] = response['prediction'][1:]

        logger.info('<<invoke>>: [{}] prediction = {}'.format(
            self.model_instance_name, json.dumps(response['prediction'], indent=4)))

        return response
