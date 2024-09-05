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
import bedrock_helpers

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    if event:
        batch_item_failures = []
        sqs_batch_response = {}
     
        for record in event.get("Records", []):
            try:
                logger.info(f'record = {json.dumps(record, indent=4)}')
                body = json.loads(record.get('body', {}))
                
                question = body.get('question', 'temp')
                answer = body.get('answer', 'temp')
                context = body.get('context', 'temp')

                logger.debug(f'question = "{question}"')
                logger.debug(f'answer = "{answer}"')
                logger.debug(f'context = "{context}"')
                
                detection_agent = bedrock_helpers.select_conversational_agent(os.environ.get('LLM'))
                
                if (detection_response := detection_agent.detect_hallucinations(question, answer, context)):
                    logger.debug(f'DETECTION RESULT = {json.dumps(detection_response, indent=4)}')
                    invocation_time = detection_response.get('invocation_time')
                    result = detection_response.get('result')
                    rationale = detection_response.get('rationale')
                    logger.info(f'detection_result = {result}, rationale = {rationale}')
    
                    output = {
                        'question': question,
                        'answer': answer,
                        'context': context,
                        'rationale': rationale,
                        'latency': invocation_time
                    }
                    
                    if result == 'CORRECT':
                        output['hallucination'] = 'FALSE'
                        logger.info(f'No hallucination detected: {json.dumps(output, indent=4)}')
                        
                    elif result == 'HALLUCINATED':
                        output['hallucination'] = 'TRUE'
                        logger.warning(f'Hallucination detected: {json.dumps(output, indent=4)}')
    
                    else:
                        output['hallucination'] = 'UNDETERMINED'
                        logger.error(f'Error in hallucination detection: {json.dumps(output, indent=4)}')

            except Exception as e:
                logger.error(f'exception: {str(e)}')
                batch_item_failures.append({"itemIdentifier": record['messageId']})
        
        sqs_batch_response["batchItemFailures"] = batch_item_failures
        logger.info(f'response = {json.dumps(sqs_batch_response, indent=4)}')
        return sqs_batch_response
