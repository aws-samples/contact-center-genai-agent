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

"""AnthropicClaudeModel"""

import json
import logging
import time
from boto3 import client
from bedrock_utils.models.bedrock_model import BedrockModel

logger = logging.getLogger()
logger.setLevel(logging.INFO)

RESPONSE_MIME_TYPE = 'application/json'
INPUT_MIME_TYPE = 'application/json'

class AnthropicClaudeModel(BedrockModel):
    CLAUDE_V1_INSTANT = 'anthropic.claude-instant-v1'
    CLAUDE_V2 = 'anthropic.claude-v2'
    CLAUDE_V2_1 = 'anthropic.claude-v2:1'
    CLAUDE_V3_HAIKU = 'anthropic.claude-3-haiku-20240307-v1:0'
    CLAUDE_V3_SONNET = 'anthropic.claude-3-sonnet-20240229-v1:0'
    CLAUDE_V3_5_SONNET = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
    CLAUDE_V3_OPUS = 'anthropic.claude-3-opus-20240229-v1:0'
    MODEL_NAMES = {
        CLAUDE_V1_INSTANT: 'Anthropic Claude Instant V1.2',
        CLAUDE_V2: 'Anthropic Claude V2',
        CLAUDE_V2_1: 'Anthropic Claude V2.1',
        CLAUDE_V3_HAIKU: 'Anthropic Claude V3 Haiku',
        CLAUDE_V3_SONNET: 'Anthropic Claude V3 Sonnet',
        CLAUDE_V3_5_SONNET: 'Anthropic Claude V3.5 Sonnet',
        CLAUDE_V3_OPUS: 'Anthropic Claude V3 Opus'
    }
    
    def __init__(
        self,
        bedrock_client: client,
        model_id: str,
        instance_name: str = None,
        temperature: float = 0.0,
        top_p: float = 1.0,
        top_k: float = 200,
        max_tokens: float = 300,
        stop_sequences: list = ['\n\nHuman:']
    ) -> None:
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
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

        if self.model_id in [self.CLAUDE_V1_INSTANT, self.CLAUDE_V2, self.CLAUDE_V2_1]:
            prompt_data = {
                "prompt": prompt,
                "temperature": temperature if temperature is not None else self.temperature,
                "top_p": top_p if top_p is not None else self.top_p,
                "top_k": top_k if top_k is not None else self.top_k,
                "max_tokens_to_sample": max_tokens if max_tokens is not None else self.max_tokens,
                "stop_sequences": stop_sequences if stop_sequences is not None else self.stop_sequences
            }
        else:
            system = None
            human = None
            assistant = None
            
            if 'Assistant:' in prompt:
                prompt, assistant = prompt.split('Assistant:', 1)
            
            if 'Human:' in prompt:
                prompt, human = prompt.split('Human:', 1)
            
            if 'System:' in prompt:
                prompt, system = prompt.rsplit('System:', 1)
                
            user = human if human else prompt

            prompt_data = {
                "anthropic_version": "bedrock-2023-05-31",
                "temperature": temperature if temperature is not None else self.temperature,
                "top_p": top_p if top_p is not None else self.top_p,
                "top_k": top_k if top_k is not None else self.top_k,
                "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
                "messages": []
            }
            if system:
                prompt_data['system'] = system.strip()
            if user:
                prompt_data['messages'].append({"role": "user", "content": user.strip()})
            if assistant:
                prompt_data['messages'].append({"role": "assistant", "content": assistant.strip()})

        response = self.invoke_bedrock_model(prompt_data, INPUT_MIME_TYPE, RESPONSE_MIME_TYPE)
        
        if self.model_id in [self.CLAUDE_V1_INSTANT, self.CLAUDE_V2, self.CLAUDE_V2_1]:
            response['prediction'] = response['full_response'].get('completion')
        else:
            content = response['full_response'].get('content',[])
            if len(content) == 0:
                response['prediction'] = None
            else:
                response['prediction'] = content[0].get('text', None)

        if not response['prediction']:
            response['error'] = 'no prediction returned'
            response['prediction'] = 'no response from LLM'
            logger.error('<<invoke>>: {}'.format(response['error']))

        if response['prediction'][:1] == ' ':
            response['prediction'] = response['prediction'][1:]

        logger.info('<<invoke>>: [{}] prediction = {}'.format(
            self.model_instance_name, json.dumps(response['prediction'], indent=4)))

        return response
