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

"""BedrockKnowledgeBases wrapper classes"""

import json
import logging
import time
from boto3 import client

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class BedrockKnowledgeBase(object):
    def __init__(
        self,
        bedrock_agent_client: client,
        kb_id: str,
        kb_instance_name: str = None,
        max_docs: int = 10,
        threshold: float = 0.40,
        metadata_filter: dict = None,
        search_type: str = 'SEMANTIC',
        s3_bucket: str = None
    ) -> None:
        self._bedrock_agent_client = bedrock_agent_client
        self._kb_id = kb_id
        self._kb_instance_name = kb_instance_name if kb_instance_name else "Default-KB"
        self._max_docs = max_docs
        self._threshold = threshold
        self._metadata_filter = metadata_filter
        self._search_type = search_type
        self._s3_bucket = s3_bucket

    def retrieve_context(
        self, 
        query: str,
        max_docs: int = None,
        threshold: float = None,
        metadata_filter: str = None,
        search_type: str = None
    ) -> dict:
        start_time = time.time()
        
        query_config = {
            'vectorSearchConfiguration': {
                'numberOfResults': max_docs if max_docs else self._max_docs,
                'overrideSearchType': search_type if search_type else self._search_type
            }
        }
        
        if metadata_filter or self._metadata_filter:
            query_config['vectorSearchConfiguration']['filter'] = \
                metadata_filter if metadata_filter else self._metadata_filter        
        
        logger.info(f'<<retrieve_context>> Bedrock KB query-config = {json.dumps(query_config, indent=4)}')

        response = self._bedrock_agent_client.retrieve(
            knowledgeBaseId = self._kb_id,
            retrievalQuery = {'text': query},
            retrievalConfiguration = query_config
        )

        num_matches = 0
        context = ''
        
        relevance_threshold = threshold if threshold else self._threshold
        
        if response:
            logger.info(f'<<retrieve_context>> Bedrock KB response = {json.dumps(response, indent=4)}')
            results = response.get('retrievalResults', [])
            for result in results:
                text = result.get('content', {}).get('text')
                source = result.get('metadata', {}).get('x-amz-bedrock-kb-source-uri')
                source = 'N/A' if source is None else source
                score = result.get('score', 0.0)

                logger.info(f'<<retrieve_context>> Bedrock KB source = {source}')
                
                prefix = '[ ]'
                if text and score:
                    if score >= relevance_threshold:
                        logger.debug(f'<<retrieve_context>> MATCH: {score:.7f} - {source}')
                        logger.debug(f'<<retrieve_context>> TEXT:  {text}')

                        prefix = '[x]'
                        num_matches += 1
                        context += text + '\n'
                        logger.info(f'<<retrieve_context>> {prefix} ({score:.7f}) {source}')
                    else:
                        logger.info(f'<<retrieve_context>> {prefix} ({score:.7f}) {source} - LOW SCORE')

                    logger.info(f'<<retrieve_context>> {json.dumps(text)}')
                    
        invocation_time = int((time.time() - start_time) * 1000)  # milliseconds
        logger.info(f'<<retrieve_context>> found {num_matches} matches in the knowledge base in {invocation_time} ms.')
        
        response = {
            'context': context if num_matches else "There is no information available on this topic.",
            'num_matches': num_matches,
            'invocation_time': invocation_time
        }
        
        return response

        
    @property
    def kb_id(self) -> str:
        return self._kb_id

    @kb_id.setter
    def kb_id(self, value: str):
        self._kb_id = value

    @property
    def kb_instance_name(self) -> str:
        return self._kb_instance_name

    @kb_instance_name.setter
    def kb_instance_name(self, value: str):
        self._kb_instance_name = value

    @property
    def max_docs(self) -> int:
        return self._max_docs

    @max_docs.setter
    def max_docs(self, value: int):
        self._max_docs = value

    @property
    def threshold(self) -> float:
        return self._threshold

    @threshold.setter
    def threshold(self, value: float):
        self._threshold = value
    
    @property
    def metadata_filter(self) -> dict:
        return self._metadata_filter

    @metadata_filter.setter
    def metadata_filter(self, value: dict):
        self._metadata_filter = value

    @property
    def search_type(self) -> str:
        return self._search_type

    @search_type.setter
    def search_type(self, value: str):
        self._search_type = value

    @property
    def s3_bucket(self) -> str:
        return self._s3_bucket

    @s3_bucket.setter
    def s3_bucket(self, value: str):
        self._s3_bucket = value

