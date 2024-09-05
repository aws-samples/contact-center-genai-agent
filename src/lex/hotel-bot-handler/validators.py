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

import re
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def validate_number(value, length):
    if len(value) != length:
        return False

    expr = '[0-9]{' + str(length) + ',' + str(length) + '}'
    digits = re.match(expr, value)
    if not digits:
        return False

    return True

def validate_amount(value):
    expr = '^[0-9.]$'
    match = re.match(expr, value)
    if not match:
        return False
    return True

def validate_alphanumeric(value, length):
    if len(value) != length:
        return False

    expr = '[0-9A-Z]{' + str(length) + ',' + str(length) + '}'
    match = re.match(expr, value)
    if not match:
        return False

    return True
    
def validate_account_id(value):
    expr = '^[A-Za-z]{2}[0-9]{3}$'
    match = re.match(expr, value)
    if not match:
        return False
    return True

def validate_date_of_service(value):
    return True

def validate_email_address(value):
    return '@' in value
