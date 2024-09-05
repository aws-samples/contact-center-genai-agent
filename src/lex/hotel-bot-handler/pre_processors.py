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

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def prefill_account_type(event, required_slot):
    sessionState = event.get('sessionState', {})
    sessionAttributes = sessionState.get("sessionAttributes", {})

    from_account = sessionAttributes.get('fromAccount', None)
    to_account = sessionAttributes.get('toAccount', None)
    last_account_mentioned = sessionAttributes.get('last_account_mentioned', None)
    
    logger.info(
        f'<<prefill_account_type({required_slot})>> - ' +
        f'last_account_mentioned = {last_account_mentioned}, ' +
        f'from_account = {from_account}, ' +
        f'to_account = {to_account}'
    )
    
    if not last_account_mentioned:
        # can't prefill if no other account was mentioned
        return None
        
    if required_slot == 'fromAccount':
        logger.info(f'<<prefill_account_type({required_slot})>> - to_account = {to_account}')
        if to_account is None or to_account != last_account_mentioned:
            return last_account_mentioned
    elif required_slot == 'toAccount':
        logger.info(f'<<prefill_account_type({required_slot})>> - from_account = {from_account}')
        if from_account is None or from_account != last_account_mentioned:
            return last_account_mentioned
            
    return None
