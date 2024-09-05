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

import json
import logging
import os
import sys
import botocore
import boto3

from bedrock_utils.knowledge_base import BedrockKnowledgeBase

from bedrock_utils.models.ai21 import (AI21LabsJurassic2Model, AI21LabsJambaModel)
from bedrock_utils.models.amazon import AmazonTitanModel
from bedrock_utils.models.anthropic import AnthropicClaudeModel
from bedrock_utils.models.cohere import CohereCommandModel
from bedrock_utils.models.meta import Llama3Model
from bedrock_utils.models.mistral import MistralAIModel

from bedrock_utils.hotel_agents.conversational_agent import ConversationalAgent
from bedrock_utils.hotel_agents.amazon import AmazonTitanConversationalAgent
from bedrock_utils.hotel_agents.anthropic import AnthropicClaude3ConversationalAgent

logger = logging.getLogger()
logger.setLevel(logging.INFO)
### uncomment below for logging output in notebooks
###logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

logger.info('<<bedrock_helpers>> boto3 version={}'.format(boto3.__version__))
logger.info('<<bedrock_helpers>> botocore version={}'.format(botocore.__version__))

bedrock_client = boto3.client('bedrock-runtime')
bedrock_agents_client = boto3.client('bedrock-agent-runtime')
sqs_client = boto3.client('sqs')

KNOWLEDGE_BASES = {
    'Alfa': BedrockKnowledgeBase(
        bedrock_agent_client = bedrock_agents_client, 
        kb_id = os.environ.get('KB_ALFA'),
        kb_instance_name = 'Alfa', 
        max_docs = 5,
        threshold = 0.40, 
        search_type = 'HYBRID',
        s3_bucket = os.environ.get('S3_BUCKET_ALFA'),
    )
    # you can add additional KBs here for testing: Bravo, Charlie, Delta, Echo, Foxtrot
}
KNOWLEDGE_BASES['Default'] = KNOWLEDGE_BASES['Alfa']

def select_knowledge_base(knowledge_base):
    if knowledge_base and len(knowledge_base) > 0:
        return KNOWLEDGE_BASES.get(knowledge_base)
    else:
        return KNOWLEDGE_BASES.get('Default')


CONVERSATIONAL_AGENTS = {
    'Jurassic 2 Mid': ConversationalAgent(
        AI21LabsJurassic2Model(bedrock_client, AI21LabsJurassic2Model.JURASSIC_2_MID, 'Jurassic 2 Mid')
    ),
    'Jurassic 2 Ultra': ConversationalAgent(
        AI21LabsJurassic2Model(bedrock_client, AI21LabsJurassic2Model.JURASSIC_2_ULTRA, 'Jurassic 2 Ultra')
    ),
    'Jamba Instruct': ConversationalAgent(
        AI21LabsJambaModel(bedrock_client, AI21LabsJambaModel.JAMBA_INSTRUCT, 'Jamba Instruct')
    ),
    'Titan Text G1 Lite': AmazonTitanConversationalAgent(
        AmazonTitanModel(bedrock_client, AmazonTitanModel.TITAN_TEXT_LITE, 'Titan Text G1 Lite')
    ),
    'Titan Text G1 Express': AmazonTitanConversationalAgent(
        AmazonTitanModel(bedrock_client, AmazonTitanModel.TITAN_TEXT_EXPRESS, 'Titan Text G1 Express')
    ),
    'Titan Text G1 Premier': AmazonTitanConversationalAgent(
        AmazonTitanModel(bedrock_client, AmazonTitanModel.TITAN_TEXT_PREMIER, 'Titan Text G1 Premier')
    ),
    'Claude V1 Instant': AnthropicClaude3ConversationalAgent(
        AnthropicClaudeModel(bedrock_client, AnthropicClaudeModel.CLAUDE_V1_INSTANT, 'Claude V1 Instant')
    ),
    'Claude V2': AnthropicClaude3ConversationalAgent(
        AnthropicClaudeModel(bedrock_client, AnthropicClaudeModel.CLAUDE_V2, 'Claude V2')
    ),
    'Claude V2.1': AnthropicClaude3ConversationalAgent(
        AnthropicClaudeModel(bedrock_client, AnthropicClaudeModel.CLAUDE_V2_1, 'Claude V2.1')
    ),
    'Claude V3 Haiku': AnthropicClaude3ConversationalAgent(
        AnthropicClaudeModel(bedrock_client, AnthropicClaudeModel.CLAUDE_V3_HAIKU, 'Claude V3 Haiku')
    ),
    'Claude V3 Sonnet': AnthropicClaude3ConversationalAgent(
        AnthropicClaudeModel(bedrock_client, AnthropicClaudeModel.CLAUDE_V3_SONNET, 'Claude V3 Sonnet')
    ),
    'Claude V3.5 Sonnet': AnthropicClaude3ConversationalAgent(
        AnthropicClaudeModel(bedrock_client, AnthropicClaudeModel.CLAUDE_V3_5_SONNET, 'Claude V3.5 Sonnet')
    ),
    'Claude V3 Opus': AnthropicClaude3ConversationalAgent(
        AnthropicClaudeModel(bedrock_client, AnthropicClaudeModel.CLAUDE_V3_OPUS, 'Claude V3 Opus')
    ),
    'Cohere Command': ConversationalAgent(
        CohereCommandModel(bedrock_client, CohereCommandModel.COHERE_COMMAND, 'Cohere Command')
    ),
    'Cohere Command Light': ConversationalAgent(
        CohereCommandModel(bedrock_client, CohereCommandModel.COHERE_COMMAND_LIGHT, 'Cohere Command Light')
    ),
    'Cohere Command R': ConversationalAgent(
        CohereCommandModel(bedrock_client, CohereCommandModel.COHERE_COMMAND_R, 'Cohere Command R')
    ),
    'Cohere Command R Plus': ConversationalAgent(
        CohereCommandModel(bedrock_client, CohereCommandModel.COHERE_COMMAND_R_PLUS, 'Cohere Command R Plus')
    ), 
    'Llama 3 8B Instruct': ConversationalAgent(
        Llama3Model(bedrock_client, Llama3Model.LLAMA3_8B_INSTRUCT, 'Llama 3 8B Instruct')
    ), 
    'Llama 3 70B Instruct': ConversationalAgent(
        Llama3Model(bedrock_client, Llama3Model.LLAMA3_70B_INSTRUCT, 'Llama 3 70B Instruct')
    ), 
    'Mistral 7B': ConversationalAgent(
        MistralAIModel(bedrock_client, MistralAIModel.MISTRAL_7B_INSTRUCT, 'Mistral 7B')
    ), 
    'Mixtral 8x7B': ConversationalAgent(
        MistralAIModel(bedrock_client, MistralAIModel.MIXTRAL_8X7B_INSTRUCT, 'Mixtral 8x7B')
    ), 
    'Mistral Small': ConversationalAgent(
        MistralAIModel(bedrock_client, MistralAIModel.MISTRAL_SMALL, 'Mistral Small')
    ), 
    'Mistral Large': ConversationalAgent(
        MistralAIModel(bedrock_client, MistralAIModel.MISTRAL_LARGE, 'Mistral Large')
    )
}
CONVERSATIONAL_AGENTS['Default'] = CONVERSATIONAL_AGENTS['Claude V3 Haiku']

# set default hyperparameters
for agent in CONVERSATIONAL_AGENTS.values():
    agent.model_instance.temperature = 0.0
    agent.model_instance.max_tokens = 1000
    
def select_conversational_agent(llm_name):
    if llm_name and len(llm_name) > 0:
        return CONVERSATIONAL_AGENTS.get(llm_name)
    else:
        return CONVERSATIONAL_AGENTS.get('Default')
    
def queue_hallucination_scan(event, question, answer, context):
    try:
        body = {'event': event, 'question': question, 'answer': answer, 'context': context}
        response = sqs_client.send_message(
            QueueUrl=os.environ.get('SQS_QUEUE_URL'),
            MessageBody=json.dumps(body)
        )
        
        if (status := response.get('ResponseMetadata', {}).get('HTTPStatusCode')) != 200:
            logger.warning(f'<<queue_hallucination_scan>> response from SQS = {json.dumps(response, indent=4)}')
        else:
            logger.info(f'<<queue_hallucination_scan>> response from SQS = {json.dumps(response, indent=4)}')

    except Exception as e:
        logger.error(f'<<queue_hallucination_scan>> exception: {str(e)}')
