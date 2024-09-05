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
import re
import dialog_helpers
import pre_processors
import post_processors
import validators

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

DEFAULT_TIMEOUT_MS = 1500

SLOT_CONFIGURATION = {
    'customerNumber': {
        'required': True,
        'slotElicitationStyle': None,
        'timeout_ms': 2000,
        'prompts': [
            {"prompt_id": "Prompt-Customer-ID-01",   "prompt": "Can you please tell me your Customer ID?"},
            {"prompt_id": "Prompt-Customer-ID-02",   "prompt": "I didn't get that, please tell me your 7-digit Customer ID."},
            {"prompt_id": "Prompt-Customer-ID-03",   "prompt": "Your Customer ID should be seven digits only. Can you try one more time?"},
              # add more here if desired
            {"prompt_id": "Prompt-Customer-ID-fail", "prompt": "Sorry, I was not able to understand your Customer ID."}
        ],
        'pre_processor': None,
        'validator': validators.validate_number,
        'validator_args': {'length': 7},
        'post_processor': None
    },
    'ragLLM': {
        'required': True,
        'slotElicitationStyle': None,
        'timeout_ms': DEFAULT_TIMEOUT_MS,
        'prompts': [
            {"prompt_id": "Prompt-LLM-Type-01",   "prompt": "Which LLM do you want to use? Claude V2 or V2.1, Claude 3 Sonnet or Haiku, Cohere, Mistral 7B or Mixtral 8x7B, Jurassic Mid or Ultra, Titan Text Lite or Express, or Llama 2?"},
            {"prompt_id": "Prompt-LLM-Type-02",   "prompt": "Let's try again. Which LLM do you want to use?"},
            {"prompt_id": "Prompt-LLM-Type-fail", "prompt": "Sorry, I was not able to understand which LLM you want."}
        ],
        'pre_processor': None,
        'validator': None,
        'validator_args': None,
        'post_processor': None
    },
    'knowledgeBase': {
        'required': True,
        'slotElicitationStyle': None,
        'timeout_ms': DEFAULT_TIMEOUT_MS,
        'prompts': [
            {"prompt_id": "Prompt-KnowledgeBase-Type-01",   "prompt": "Which knowledge base do you want to use? Titan Full Page, Titan Half Page, Cohere Full Page, Cohere Half Page, or Open Search?"},
            {"prompt_id": "Prompt-KnowledgeBase-Type-02",   "prompt": "Let's try again. Which knowledge base do you want to use?"},
            {"prompt_id": "Prompt-KnowledgeBase-Type-fail", "prompt": "Sorry, I was not able to understand which knowledge base you want."}
        ],
        'pre_processor': None,
        'validator': None,
        'validator_args': None,
        'post_processor': None
    },
    'slotName': {
        'required': True,
        'slotElicitationStyle': None,
        'timeout_ms': DEFAULT_TIMEOUT_MS,
        'prompts': [
            {"prompt_id": "Prompt-Slot-Name-01",   "prompt": "Which slot do you want me to prompt for? The Dasher ID, from account, to account, or transfer amount?"},
            {"prompt_id": "Prompt-Slot-Name-02",   "prompt": "Let's try again. Which slot would you like me to prompt you for?"},
            {"prompt_id": "Prompt-Slot-Name-fail", "prompt": "Sorry, I was not able to understand the slot type."}
        ],
        'pre_processor': None,
        'validator': None,
        'validator_args': None,
        'post_processor': None
    },
    'contextSwitch': {
        'required': True,
        'slotElicitationStyle': None,
        'timeout_ms': DEFAULT_TIMEOUT_MS,
        'prompts': [
            {"prompt_id": "Prompt-Context-Switch-01",   "prompt": "Do you want the LLM context on or off?"},
            {"prompt_id": "Prompt-Context-Switch-02",   "prompt": "Let's try again. Please say on or off."},
            {"prompt_id": "Prompt-Context-Switch-fail", "prompt": "Sorry, I was not able to understand the context switch setting."}
        ],
        'pre_processor': None,
        'validator': None,
        'validator_args': None,
        'post_processor': None
    },
    'guardrailsSwitch': {
        'required': True,
        'slotElicitationStyle': None,
        'timeout_ms': DEFAULT_TIMEOUT_MS,
        'prompts': [
            {"prompt_id": "Prompt-Guardrails-Switch-01",   "prompt": "Do you want the LLM guardrails on or off?"},
            {"prompt_id": "Prompt-Guardrails-Switch-02",   "prompt": "Let's try again. Please say on or off."},
            {"prompt_id": "Prompt-Guardrails-Switch-fail", "prompt": "Sorry, I was not able to understand the guardrails switch setting."}
        ],
        'pre_processor': None,
        'validator': None,
        'validator_args': None,
        'post_processor': None
    },
    'brand': {
        'required': False,
        'slotElicitationStyle': None,
        'timeout_ms': DEFAULT_TIMEOUT_MS,
        'prompts': [
            {"prompt_id": "Prompt-Brand-01",    "prompt": "Which of our hotel brands are you interested in?"},
            {"prompt_id": "Prompt-Brand-02",    "prompt": "I didn't catch that. Which brand? We have Luxury Suites, Seaside Resorts, Waypoint Inns, Family Getaways, and Party Times."},
            {"prompt_id": "Prompt-Brand-03",    "prompt": "Sorry, one last try. Can you please tell me which brand you're interested in?"},
            {"prompt_id": "Prompt-Brand-fail",  "prompt": "Sorry, I was not able to understand. Let me get you to an agent."}
            ### route_to_agent!  how
        ],
        'pre_processor': None,
        'validator': validators.validate_number,
        'validator_args': {'length': 5},
        'post_processor': None
    }
}

def confirm_required_slots(event, required_slots):
    """
    This function checks for each required slot, copies the available required 
    slots to session attributes, and if necessary, returns a slot elicitation
    response. If all required slots are available, it returns None.
    """
    requestAttributes = event.get("requestAttributes", {})
    sessionState = event.get('sessionState', {})
    sessionAttributes = sessionState.get("sessionAttributes", {})
    activeContexts = sessionState.get("activeContexts", [])
    intent = sessionState.get("intent", {})
    intent_name = intent['name']
    slot_values = intent.get('slots', {})
    
    # first, collect any available slot values into session attributes
    for required_slot in required_slots:
        if not (slot_config := SLOT_CONFIGURATION.get(required_slot)):
            error_message = f'Configuration error - no slot configuration for {required_slot}'
            logger.error(f'<<confirm_required_slots>> {error_message}')
            response_message = dialog_helpers.format_message_array(error_message, 'PlainText')
            response = dialog_helpers.close(intent, activeContexts, sessionAttributes, response_message, requestAttributes)
            return response

        # check for the session attribute already captured
        required_slot_attribute = sessionAttributes.get(required_slot, '')
        
        if required_slot_attribute == '':
            # check for the slot value
            required_slot_value = None
            if slot := slot_values.get(required_slot):
                if slot.get('value'):
                    if slot_value := slot['value'].get('interpretedValue'):
                        if validator_function := slot_config.get('validator'):
                            args = {'value': slot_value} 
                            if validator_args := slot_config.get('validator_args'):
                                # add additional validator parameters, if any
                                args |= validator_args
                            if validator_function(**args):
                                required_slot_value = slot_value
                        else:
                            required_slot_value = slot_value
            
            if required_slot_value:
                if post_processor := slot_config.get('post_processor'):
                    required_slot_value = post_processor(required_slot_value)
        
            logger.info('<<confirm_required_slots>> - Required slot {}: attribute = {}, slot = {}'.format(
                required_slot, 
                required_slot_attribute if required_slot_attribute is not None else '<none>',
                required_slot_value if required_slot_value is not None else '<none>'
            ))
            
            if required_slot_value:
                sessionAttributes[required_slot] = required_slot_value
                if sessionAttributes.get(required_slot + '_retries'):
                    del sessionAttributes[required_slot + '_retries']


    # now, elicit for the next needed slot if necessary
    for required_slot in required_slots:
        required_slot_attribute = sessionAttributes.get(required_slot, '')

        if required_slot_attribute == '':
            slot_config = SLOT_CONFIGURATION.get(required_slot)
            
            # see if slot can be pre-filled based on business logic
            if pre_processor := slot_config.get('pre_processor'):
                required_slot_attribute = pre_processor(event, required_slot)
                
                if required_slot_attribute:
                    logger.info(f'pre-filled required slot {required_slot} with value {required_slot_attribute}')
                    sessionAttributes[required_slot] = required_slot_attribute
                    if sessionAttributes.get(required_slot + '_retries'):
                        del sessionAttributes[required_slot + '_retries']
                    return None
            
            # set the "end silence threshold" timeout
            timeout_attribute = 'x-amz-lex:audio:end-timeout-ms:' + intent_name + ':' + '*'  # replace intent_name with '*' for less log data
            sessionAttributes[timeout_attribute] = slot_config.get('timeout_ms')
    
            # elicit for the slot
            if slot_config.get('required', False):
                logger.info('<<{}>> - Eliciting slot {}'.format(intent_name, required_slot)) 
                response = dialog_helpers.elicit_slot_with_retries(intent, activeContexts, sessionAttributes, 
                    required_slot, requestAttributes, SLOT_CONFIGURATION)
                logger.info('<<{}>> elicitSlot response = {}'.format(intent_name, json.dumps(response)))
                return response
    
    # all required slots available
    return None


REMOVE_WHITESPACE = re.compile('\n *') 

def remove_whitespace(template):
    response = re.sub(REMOVE_WHITESPACE, ' ', template)
    response = response.strip()
    return response


def build_response(template, data):
    response = remove_whitespace(template)
    try:
        response = response.format(**data)
    except KeyError as e:
        response = "Missing data element '{}'".format(e)
        
    return response
