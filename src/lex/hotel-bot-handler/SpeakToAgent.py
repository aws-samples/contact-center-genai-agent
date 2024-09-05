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

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TRANSFER_TO_AGENT_RESPONSE = "Transfer-To-Agent-Response"

RESPONSE_TYPES = {
    TRANSFER_TO_AGENT_RESPONSE: """
        OK, let me get you to an agent to help.
        """,
    # additional response types here as needed
}

def lambda_handler(event, context):
    
    requestAttributes = event.get("requestAttributes", {})
    sessionState = event.get('sessionState', {})
    sessionAttributes = sessionState.get("sessionAttributes", {})
    activeContexts = sessionState.get("activeContexts", [])
    intent = sessionState.get("intent", {})
    intent_name = intent['name']

    logger.info('<<{}>> - Lex event info {} '.format(intent_name, json.dumps(event)))

    response_data = {}
    
    sessionAttributes['prompt_id'] = TRANSFER_TO_AGENT_RESPONSE
    response_template = RESPONSE_TYPES.get(TRANSFER_TO_AGENT_RESPONSE, f"{TRANSFER_TO_AGENT_RESPONSE} not found")
    response_template = slot_configuration.remove_whitespace(response_template)
    sessionAttributes['prompt'] = response_template
    sessionAttributes['sendToAgent'] = '1'

    response_string = slot_configuration.build_response(response_template, response_data)

    response_message = dialog_helpers.format_message_array(response_string, 'PlainText')
    intent['state'] = 'Fulfilled'
    response = dialog_helpers.close(intent, activeContexts, sessionAttributes, response_message, requestAttributes)

    logger.info('<<{}>>: response = {} '.format(intent_name, json.dumps(response)))

    return response
