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

import logging
import json
import dialog_helpers
import slot_configuration
import bedrock_helpers
import re
import time

import TopicIntentHandler

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

USE_LLM = True

def lambda_handler(event, context):
    requestAttributes = event.get("requestAttributes", {})
    sessionState = event.get('sessionState', {})
    sessionAttributes = sessionState.get("sessionAttributes", {})
    activeContexts = sessionState.get("activeContexts", [])
    intent = sessionState.get("intent", {})
    intent_name = intent['name']
    slot_values = intent.get('slots', {})

    logger.info('<<{}>> - Lex event info {} '.format(intent_name, json.dumps(event)))

    # if caller says nothing, keep waiting (say nothing back!)
    if event.get('inputMode') == 'Speech':
        if len(event.get('inputTranscript')) == 0:
            logger.info('<<{}>> empty speech input transcript (timed out)'.format(intent_name))
            time.sleep(2)
            response_message = dialog_helpers.format_message_array('<speak></speak>', 'SSML')
            intent['state'] = 'Fulfilled'
            response = dialog_helpers.close(intent, activeContexts, sessionAttributes, response_message, requestAttributes)
            logger.info('<<{}>>: response = {}'.format(intent_name, json.dumps(response)))
            return response

    if USE_LLM:
        return TopicIntentHandler.lambda_handler(event, context)
        
    else:
        response_data = {}
        
        sessionAttributes['prompt_id'] = "Fallback-Message"
        response_string = "Sorry, I didn't understand. Can you try again?"
        sessionAttributes['prompt'] = response_string
    
        if event.get('inputMode', '') == 'Speech':
            response_string = '<speak>' + response_string + '</speak>'

        response_message = dialog_helpers.format_message_array(response_string, 'PlainText')
    
        intent['state'] = 'Fulfilled'
        response = dialog_helpers.close(intent, activeContexts, sessionAttributes, response_message, requestAttributes)
        logger.info('<<{}>>: response = {}'.format(intent_name, json.dumps(response)))
    
        return response
