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

import boto3
import json
import cfnresponse

import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client('connect')

# --- Main handler ---
def lambda_handler(event, context):
    logger.info('<<lambda_handler>>: EVENT = {}'.format(json.dumps(event)))

    request_type = event.get('RequestType')
    contact_name = event['ResourceProperties'].get('ContactName')
    response_id = event.get('RequestId')
    instance_arn = event['ResourceProperties'].get('ConnectInstanceArn')
    instance_id = parse_arn(instance_arn).get('resource')
    
    try:
        if request_type == 'Create':
            logger.info('<<lambda_handler>>: create contact flow')
            create_contact_flow(event, context)
    
        elif request_type == 'Update':
            logger.info('<<lambda_handler>>: update contact flow')
            delete_contact_flow(event, context)
            delete_contact_flow_resources(event, context)
            create_contact_flow(event, context)
    
        elif request_type == 'Delete':
            logger.info('<<lambda_handler>>: delete contact flow')
            delete_contact_flow(event, context)
            delete_contact_flow_resources(event, context)

            reason = 'Contact flow deleted'
            response_status = cfnresponse.SUCCESS
            response = {}
            response['ContactFlowDescription'] = reason
            cfnresponse.send(event, context, response_status, response, response_id, reason)

    except client.exceptions.DuplicateResourceException as e:
        response_id = event.get('RequestId')
        reason = "Contact flow '"+contact_name+"' already exists. Exception: "+ str(e)
        logger.error('<<lambda_handler>>: error: ' + reason)
        cfnresponse.send(event, context, cfnresponse.FAILED, {}, response_id, reason)

    except client.exceptions.InvalidRequestException as e:
        response_id = event.get('RequestId')
        reason = "Contact flow '"+contact_name+"' was not created because of the following exception: "+ str(e)
        logger.error('<<lambda_handler>>: error: ' + reason)
        cfnresponse.send(event, context, cfnresponse.FAILED, {}, response_id, reason)

        response_id = event.get('RequestId')
        reason = "Connect instance id: '"+instance_id+"' does not exist, so the contact flow was not created. You can test on Lex V2 console."
        response = {}
        response['ContactFlowDescription'] = reason
        logger.error('<<lambda_handler>>: error: ' + reason)
        cfnresponse.send(event, context, cfnresponse.SUCCESS, response, response_id, reason)

    except (client.exceptions.InvalidParameterException,
            client.exceptions.ResourceNotFoundException) as e:
        response_id = event.get('RequestId')
        reason = "Contact flow '"+contact_name+"' was not created because of the following exception: "+ str(e)
        logger.error('<<lambda_handler>>: error: ' + reason)
        cfnresponse.send(event, context, cfnresponse.FAILED, {}, response_id, reason)
            
    except Exception as e:
        response_id = event.get('RequestId')
        reason = "Contact flow '"+contact_name+"' was not created because of the following exception: "+ str(e)
        logger.error('<<lambda_handler>>: error: ' + reason)
        cfnresponse.send(event, context, cfnresponse.FAILED, {}, response_id, reason)


def create_contact_flow(event, context):
    logger.info('<<create_contact_flow>>')

    request_type = event.get('RequestType')
    bot_name = event['ResourceProperties'].get('BotName')
    bot_name2 = event['ResourceProperties'].get('BotName2')
    bot_alias_arn = event['ResourceProperties'].get('BotAliasArn')
    bot_alias_arn2 = event['ResourceProperties'].get('BotAliasArn2')
    instance_arn = event['ResourceProperties'].get('ConnectInstanceArn')
    contact_name = event['ResourceProperties'].get('ContactName')
    response_id = event.get('RequestId')
    instance_id = parse_arn(instance_arn).get('resource')
    
    if not instance_id:
        response_id = event.get('RequestId')
        reason = "The contact flow was not created. You can test on the Lex V2 console."
        response = {}
        response['ContactFlowDescription'] = reason
        logger.info('<<create_contact_flow>> ' + reason)
        cfnresponse.send(event, context, cfnresponse.SUCCESS, response, response_id, reason)

    else:
        logger.info('<<create_contact_flow>>: creating new contact flow')

        associate_bot(instance_id, bot_alias_arn)
        if bot_alias_arn2:
            associate_bot(instance_id, bot_alias_arn2)
            
        status = import_contact_flow(
            instance_id, contact_name, bot_alias_arn, bot_alias_arn2, bot_name, bot_name2
        )
        if status == 'SUCCESS':
            response = {}
            response['ContactFlowDescription'] = \
                "Contact flow "+ contact_name+ " was created successfully"
            reason = 'Imported contact flow successfully'
            cfnresponse.send(event, context, cfnresponse.SUCCESS, response, response_id, reason)
        else:
            response = {}
            response['ContactFlowDescription'] = \
                "Contact flow "+ contact_name+ " creation failed"
            cfnresponse.send(event, context, cfnresponse.SUCCESS, response, response_id, 'Contact flow import failed')


def delete_contact_flow(event, context):
    logger.info('<<delete_contact_flow>>')
    
    request_type = event.get('RequestType')
    response_id = event.get('RequestId')

    if request_type == 'Delete':
        resource_properties = 'ResourceProperties'
    elif request_type == 'Update':
        resource_properties = 'OldResourceProperties'
    else:
        reason = 'Request type error'
        response_status = cfnresponse.FAILED
        response = {}
        response['ContactFlowDescription'] = reason
        cfnresponse.send(
                event, context, response_status, response, response_id, reason)
        return
    
    contact_name = event[resource_properties].get('ContactName')
    instance_arn = event[resource_properties].get('ConnectInstanceArn')
    instance_id = parse_arn(instance_arn).get('resource')
    bot_alias_arn = event[resource_properties].get('BotAliasArn')
    bot_alias_arn2 = event[resource_properties].get('BotAliasArn2')

    logger.info('<<delete_contact_flow>> delete flow name = {}'.format(contact_name))
    
    response = client.list_contact_flows(InstanceId=instance_id, MaxResults=100)
    
    logger.info('<<delete_contact_flow>>: list_contact_flows response = {}'.format(json.dumps(response)))

    flow_id_to_delete = None
    next_token = response.get('NextToken', 'start')
    while next_token is not None:
        contact_flows = response.get('ContactFlowSummaryList', [])
        for flow in contact_flows:
            # logger.info('<<delete_contact_flow>> checking flow name = {}'.format(flow['Name']))
            if flow.get('Name', '') == contact_name:
                flow_id_to_delete = flow.get('Id', None)
                break
        next_token = response.get('NextToken', None)
        # logger.info('<<delete_contact_flow>>: next_token = {}'.format(next_token))

        if next_token is not None:
            response = client.list_contact_flows(InstanceId=instance_id, NextToken=next_token, MaxResults=100)
            logger.info('<<delete_contact_flow>>: list_contact_flows response = {}'.format(json.dumps(response)))

    logger.info('<<delete_contact_flow>>: flow ID to delete = {}'.format(flow_id_to_delete))
    
    if flow_id_to_delete is not None:
        response = client.delete_contact_flow(InstanceId=instance_id, ContactFlowId=flow_id_to_delete)
        logger.info('<<delete_contact_flow>>: delete_contact_flow response = {}'.format(json.dumps(response)))


def delete_contact_flow_resources(event, context):
    logger.info('<<delete_contact_flow_resources>>')
    
    request_type = event.get('RequestType')
    response_id = event.get('RequestId')

    if request_type == 'Delete':
        resource_properties = 'ResourceProperties'
    elif request_type == 'Update':
        return
    else:
        reason = 'Request type error'
        response_status = cfnresponse.FAILED
        response = {}
        response['ContactFlowDescription'] = reason
        cfnresponse.send(
                event, context, response_status, response, response_id, reason)
        return
    
    instance_arn = event[resource_properties].get('ConnectInstanceArn')
    instance_id = parse_arn(instance_arn).get('resource')
    bot_alias_arn = event[resource_properties].get('BotAliasArn')
    bot_alias_arn2 = event[resource_properties].get('BotAliasArn2')

    if bot_alias_arn:
        disassociate_bot(instance_id, bot_alias_arn)
    if bot_alias_arn2:
        disassociate_bot(instance_id, bot_alias_arn2)


def import_contact_flow(
        instance_id, contact_name, bot_alias_arn, bot_alias_arn2,
        bot_name, bot_name2):
    logger.info('<<import_contact_flow>>')
    f = open('contact_flow.json',)

    data = json.load(f)

    logger.info('<<import_contact_flow>>: input data = {}'.format(json.dumps(data)))

    str_data = json.dumps(data)
    str_data = str_data.replace('<<bot_name>>', bot_name)
    str_data = str_data.replace('<<bot_alias>>', bot_alias_arn)
    str_data = str_data.replace('<<bot_name2>>', bot_name2)
    str_data = str_data.replace('<<bot_alias2>>', bot_alias_arn2)
    data = json.loads(str_data)

    '''
    actions = data.get('Actions')
    action_metadata = data.get('Metadata').get('ActionMetadata')
    for key, value in action_metadata.items():
        if value.get('lexV2BotName') == '<<bot_name>>':
            value['lexV2BotName'] = bot_name
            identifier = [d for d in actions if d['Identifier'] == key]
            if identifier and len(identifier) > 0:
                identifier[0]['Parameters']['LexV2Bot']['AliasArn'] = bot_alias_arn

        if bot_name2 and value.get('lexV2BotName') == '<<bot_name2>>':
            value['lexV2BotName'] = bot_name2
            identifier = [d for d in actions if d['Identifier'] == key]
            if identifier and len(identifier) > 0:
                identifier[0]['Parameters']['LexV2Bot']['AliasArn'] = \
                    bot_alias_arn2
    '''

    logger.info('<<import_contact_flow>>: updated data = {}'.format(json.dumps(data)))

    response = client.create_contact_flow (
        InstanceId=instance_id,
        Name=contact_name,
        Type='CONTACT_FLOW',
        Description='Sample flow to demonstrate RAG-based Q&A via Amazon Bedrock',
        Content=json.dumps(data)
    )
    if response:
        return 'SUCCESS'
    return 'FAILED'


def parse_arn(arn):
    try:
        elements = arn.split(':', 5)
        result = {
            'arn': elements[0],
            'partition': elements[1],
            'service': elements[2],
            'region': elements[3],
            'account': elements[4],
            'resource': elements[5],
            'resource_type': None
        }
        if '/' in result['resource']:
            result['resource_type'], result['resource'] = result['resource'].split('/',1)
        elif ':' in result['resource']:
            result['resource_type'], result['resource'] = result['resource'].split(':',1)
        return result
    except:
        return {}


def associate_bot(instance_id, bot_alias_arn):
    logger.info('<<associate_bot>>: adding bot = {} to connect instance {}'.format(bot_alias_arn, instance_id))
    
    try:
        response = client.associate_bot(
            InstanceId=instance_id,
            LexV2Bot={
                'AliasArn': bot_alias_arn
            }
        )
        logger.info('<<associate_bot>>: response = {}'.format(json.dumps(response)))
    except Exception as e:
        logger.info('<<associate_bot>>: exception: {}'.format(str(e)))


def disassociate_bot(instance_id, bot_alias_arn):
    logger.info('<<disassociate_bot>>: removing bot = {} from connect instance {}'.format(bot_alias_arn, instance_id))
    
    try:
        response = client.disassociate_bot(
            InstanceId=instance_id,
            LexV2Bot={
                'AliasArn': bot_alias_arn
            }
        )
        logger.info('<<disassociate_bot>>: response = {}'.format(json.dumps(response)))
    except Exception as e:
        logger.info('<<disassociate_bot>>: exception: {}'.format(str(e)))
    
    
