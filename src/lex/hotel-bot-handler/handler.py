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

import TopicIntentHandler
import FallbackIntent
import Goodbye
import Help
import SelectLLM
import SelectKnowledgeBase
import SpeakToAgent
import ToggleLLMContext
import ToggleLLMGuardrails

import bedrock_helpers

logger = logging.getLogger()
logger.setLevel(logging.INFO)

HANDLERS = {
    'Accommodations':          {'handler': TopicIntentHandler.lambda_handler},
    'Amenities':               {'handler': TopicIntentHandler.lambda_handler},
    'BrandPortfolio':          {'handler': TopicIntentHandler.lambda_handler},
    'CorporateLoyaltyProgram': {'handler': TopicIntentHandler.lambda_handler},
    'CorporateOverview':       {'handler': TopicIntentHandler.lambda_handler},
    'CorporateSustainability': {'handler': TopicIntentHandler.lambda_handler},
    'Locations':               {'handler': TopicIntentHandler.lambda_handler},
    'Parking':                 {'handler': TopicIntentHandler.lambda_handler},
    'Policies':                {'handler': TopicIntentHandler.lambda_handler},
    'Services':                {'handler': TopicIntentHandler.lambda_handler},
    'SwitchBrand':             {'handler': TopicIntentHandler.lambda_handler},
    'Welcome':                 {'handler': TopicIntentHandler.lambda_handler},

    'FallbackIntent':          {'handler': FallbackIntent.lambda_handler},

    'Booking':                 {'handler': SpeakToAgent.lambda_handler},
    'SpeakToAgent':            {'handler': SpeakToAgent.lambda_handler},

    'Help':                    {'handler': Help.lambda_handler},
    'Goodbye':                 {'handler': Goodbye.lambda_handler},

    'SelectLLM':               {'handler': SelectLLM.lambda_handler},
    'SelectKnowledgeBase':     {'handler': SelectKnowledgeBase.lambda_handler},
    'ToggleLLMContext':        {'handler': ToggleLLMContext.lambda_handler},
    'ToggleLLMGuardrails':     {'handler': ToggleLLMGuardrails.lambda_handler}
}

def lambda_handler(event, context):
    logger.info('<<handler>>: Lex event info = ' + json.dumps(event))
    
    requestAttributes = event.get("requestAttributes", {})
    sessionState = event.get('sessionState', {})
    sessionAttributes = sessionState.get("sessionAttributes", {})
    activeContexts = sessionState.get("activeContexts", [])
    intent = sessionState.get("intent", {})
    intent_name = intent['name']

    logger.debug('<<handler>> handler function intent_name \"%s\"', intent_name)

    if intent_name in HANDLERS:
        logger.debug('<<handler>> handler function: routing to intent %s', intent_name)
        
        # clean up session attributes
        sessionAttributes = clear_session_attributes(sessionAttributes)

        # track the prior prompt for analysis purposes
        if prior_prompt_id := sessionAttributes.get('prompt_id'):
            sessionAttributes['prior_prompt_id'] = prior_prompt_id
            del sessionAttributes['prompt_id']
        else:
            sessionAttributes['prior_prompt_id'] = "Start-Conversation"

        # set initial prompt information for start of conversation
        if prior_prompt := sessionAttributes.get('prompt'):
            sessionAttributes['prior_prompt'] = prior_prompt
            del sessionAttributes['prompt']
        else:
            sessionAttributes['prior_prompt'] = "(start of conversation)"

        # set some default values
        if not sessionAttributes.get('ragLLM'):
            sessionAttributes['ragLLM'] = 'Default'
            
        if not sessionAttributes.get('knowledgeBase'):
            sessionAttributes['knowledgeBase'] = 'Default'
            
        if not sessionAttributes.get('context_switch'):
            sessionAttributes['context_switch'] = '1'
            
        if not sessionAttributes.get('guardrails_switch'):
            sessionAttributes['guardrails_switch'] = '1'

        # delegate to the intent handler
        event['sessionState']['sessionAttributes'] = sessionAttributes
        response = HANDLERS[intent_name]['handler'](event, context)

        logger.info('<<handler>>: delegated intent handler response = {}'.format(json.dumps(response)))
        
        if (retrieved_context := response.get('_retrieved_context')):
            logger.debug(f'RETRIEVED_CONTEXT = {retrieved_context}')
            del response['_retrieved_context']
        
        # manage contexts
        response = clear_inactive_contexts(response)

        # if this is a test case, run the test + hallucination detection
        if (ground_truth := sessionAttributes.get('ground-truth')):
            input_transcript = event.get('inputTranscript')
            rag_response = response['messages'][0]['content']

            if (evaluation_agent := bedrock_helpers.select_conversational_agent(sessionAttributes.get('evaluationLLM'))):
                if (evaluation_response := evaluation_agent.evaluate_response(input_transcript, rag_response, ground_truth)):
                    logger.debug(f'EVALUATION RESULT = {json.dumps(evaluation_response, indent=4)}')
                    time_in_ms = evaluation_response.get('invocation_time')
                    result = evaluation_response.get('result')
                    rationale = evaluation_response.get('rationale')
                    logger.info(f'evaluation_result = {result}, rationale = {rationale}')
                    sessionAttributes['evaluation_result'] = result
                    sessionAttributes['evaluation_details'] = rationale
                    sessionAttributes['evaluation_latency'] = time_in_ms
                    sessionAttributes['evaluation_llm'] = evaluation_agent.model_instance.model_id

            if (detection_agent := bedrock_helpers.select_conversational_agent(sessionAttributes.get('detectionLLM'))):
                  if (detection_response := detection_agent.detect_hallucinations(input_transcript, rag_response, retrieved_context)):
                    logger.debug(f'DETECTION RESULT = {json.dumps(detection_response, indent=4)}')
                    time_in_ms = detection_response.get('invocation_time')
                    result = detection_response.get('result')
                    rationale = detection_response.get('rationale')
                    logger.info(f'detection_result = {result}, rationale = {rationale}')
                    sessionAttributes['detection_result'] = result
                    sessionAttributes['detection_details'] = rationale
                    sessionAttributes['detection_latency'] = time_in_ms
                    sessionAttributes['detection_llm'] = detection_agent.model_instance.model_id


        logger.info(f'<<handler>> handler response: {json.dumps(response)}')
        return response

    else:
        error_message = f'Configuration error - no intent handler for {intent_name}'
        logger.error(f'<<handler>> handler function: {error_message}')
        response = {
            'messages': [{'contentType': 'PlainText', 'content': error_message}],
            'requestAttributes': requestAttributes,
            'sessionState': {
                'activeContexts': activeContexts,
                'intent': intent,
                'sessionAttributes': sessionAttributes,
                'dialogAction': {'type': 'Close'}
            }
        }
        logger.error(f'<<handler>> handler error response: {json.dumps(response)}')
        return response


def clear_inactive_contexts(response):
    sessionState = response.get('sessionState', {})
    activeContexts = sessionState.get('activeContexts', [])
    
    for context in activeContexts:
        name = context['name']
        turnsToLive = context['timeToLive'].get('turnsToLive', 0)
        timeToLiveInSeconds = context['timeToLive'].get('timeToLiveInSeconds', 0)
        if turnsToLive <= 0 or timeToLiveInSeconds <= 0:
            activeContexts = [i for i in activeContexts if i.get('name', '') != name]
    
    response['sessionState']['activeContexts'] = activeContexts
    return response


def clear_session_attributes(sessionAttributes):
    delete_list = (
        'rag_request_id', 'rag_input_tokens', 'rag_output_tokens', 
        'retrieval_latency', 'rag_latency', 'total_latency'
    )
    return {k: sessionAttributes[k] for k in sessionAttributes if k not in delete_list}
