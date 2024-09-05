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

"""The BedrockModels wrapper classes normalize the interfaces Bedrock foundation models

There are six wrapper classes:
 - AmazonTitanModel
 - AI21LabsJurassic2Model
 - AnthropicClaudeModel
 - CohereCommandModel
 - Llama2Model
 - MistralAIModel

You can create an instance for a particular model, and specify default parameters
such as temperature, max_tokens, top_p, etc.

Instantion and invoke methods use a common interface:

    instance.invoke(
        prompt,
        temperature,       # optional - all models
        top_p,             # optional - all models
        max_tokens,        # optional - all models
        stop_sequences,    # optional - all models
        top_k,             # optional - Claude only
        count_penalty,     # optional - Jurassic only
        presence_penalty,  # optional - Jurassic only
        frequency_penalty, # optional - Jurassic only
        return_likelihoods # optional - Cohere only
    )

Output is also normalized by providing a consistent JSON document structure:

    {
        "full_response": { <model specific> },
        "prediction": "Hello, world!",
        "input_tokens": 9,
        "output_tokens": 6
        "invocation_time_ms": 205,
    }

Note: these helper classes can be used independently, or in conjunction with LLM
frameworks such as LangChain (https://python.langchain.com/en/latest/index.html).

"""

import json
import logging
import time
from boto3 import client

logger = logging.getLogger()
logger.setLevel(logging.INFO)

RESPONSE_MIME_TYPE = 'application/json'
INPUT_MIME_TYPE = 'application/json'

class BedrockModel(object):
    MODEL_NAMES = {}

    def __init__(self, bedrock_client: client, model_id: str, instance_name: str = None) -> None:
        self._bedrock_client = bedrock_client
        self._model_id = model_id
        self._instance_name = instance_name if instance_name else self.model_name()
        
    def invoke(self, prompt: str, model_id: str, instance_name: str) -> None:
        pass
    
    def invoke_bedrock_model(
        self,
        prompt_data: dict,
        input_mime_type: str,
        response_mime_type: str,
    ) -> dict:
        logger.info('<<invoke_bedrock_model>>: [{}] model_id = {}, prompt = {}'.format(
            self.model_instance_name, self._model_id, json.dumps(prompt_data, indent=4)))
        
        body = json.dumps(prompt_data)

        start_time = time.time()

        response = None
        try:
            bedrock_response = self._bedrock_client.invoke_model(
                body=body, modelId=self._model_id, accept=response_mime_type, contentType=input_mime_type
            )
        except Exception as e:
            logger.error('<<invoke_bedrock_model>>: EXCEPTION: {}'.format(e))
            raise e

        invocation_time = int((time.time() - start_time) * 1000)  # milliseconds

        if not bedrock_response:
            logger.error('<<invoke_bedrock_model>>: EXCEPTION: no response from model')
            raise RuntimeError('no response from model')

        response_metadata = bedrock_response.get('ResponseMetadata', {}).get('HTTPHeaders')

        response_body = json.loads(bedrock_response.get('body').read())

        logger.info('<<invoke_bedrock_model>>: [{}] response = {}'.format(
            self.model_instance_name, json.dumps(response_body, indent=4)))
        logger.debug('<<invoke_bedrock_model>>: [{}] invocation time = {} ms'.format(
            self.model_instance_name, invocation_time))
        
        response = {
            'full_response': response_body, 
            'invocation_time': invocation_time
        }

        if response_metadata:
            response['request_id'] = response_metadata.get('x-amzn-requestid')
            response['invocation_latency'] = int(response_metadata.get('x-amzn-bedrock-invocation-latency'))
            response['input_tokens'] = int(response_metadata.get('x-amzn-bedrock-input-token-count'))
            response['output_tokens'] = int(response_metadata.get('x-amzn-bedrock-output-token-count'))
        
        return response
        
    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def model_name(self) -> str:
        return type(self).MODEL_NAMES.get(self._model_id, 'NO-MODEL')

    @property
    def model_instance_name(self) -> str:
        if self._instance_name is None:
            return self.model_name + ' (' + self._model_id + ')'
        else:
            return self._instance_name + ' (' + self._model_id + ')'
