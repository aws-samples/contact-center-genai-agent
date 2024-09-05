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
import random
import datetime
import dialog_helpers
import slot_configuration

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TOGGLE_LLM_CONTEXT_SUCCESS = "Toggle-LLM-Context-Success"

RESPONSE_TYPES = {
    TOGGLE_LLM_CONTEXT_SUCCESS: """
        OK, changed the LLM context setting to {context_switch}.
        """
}

REQUIRED_SLOTS = ['contextSwitch']

def lambda_handler(event, context):

    requestAttributes = event.get("requestAttributes", {})
    sessionState = event.get('sessionState', {})
    sessionAttributes = sessionState.get("sessionAttributes", {})
    activeContexts = sessionState.get("activeContexts", [])
    intent = sessionState.get("intent", {})
    intent_name = intent['name']
    slot_values = intent.get('slots', {})
    
    logger.info('<<{}>> - Lex event info {} '.format(intent_name, json.dumps(event)))
    
    if sessionAttributes.get('contextSwitch'):
        del sessionAttributes['contextSwitch']
    
    if response := slot_configuration.confirm_required_slots(event, REQUIRED_SLOTS):
        return response

    context_switch = sessionAttributes.get('contextSwitch')
    
    if context_switch == 'on':
        sessionAttributes['context_switch'] = '1'
    elif context_switch == 'off':
        sessionAttributes['context_switch'] = '0'
    else:
        sessionAttributes['context_switch'] = '1'
    
    response_data = {}
    response_data['context_switch'] = context_switch

    sessionAttributes['prompt_id'] = TOGGLE_LLM_CONTEXT_SUCCESS
    response_template = RESPONSE_TYPES.get(TOGGLE_LLM_CONTEXT_SUCCESS, f"{TOGGLE_LLM_CONTEXT_SUCCESS} not found")

    response_template = slot_configuration.remove_whitespace(response_template)
    sessionAttributes['prompt'] = response_template

    if event.get('inputMode', '') == 'Text':
        response_string = slot_configuration.build_response(response_template, response_data)
    else:
        response_string = '<speak>' + slot_configuration.build_response(response_template, response_data) + '</speak>'

    response_message = dialog_helpers.format_message_array(response_string, 'PlainText')

    intent['state'] = 'Fulfilled'
    response = dialog_helpers.close(intent, activeContexts, sessionAttributes, response_message, requestAttributes)

    logger.info('<<{}>>: response = {}'.format(intent_name, json.dumps(response)))

    return response


