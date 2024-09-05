# Contact Center GenAI Assistant

**_An automated question answering solution for contact centers, optimized for both text and voice._** 

# Contents
- [Overview](#overview)
- [Deploy and test the solution](#deploy-and-test-the-solution)
    - [Step 1: Deploy the Knowledge Base stack](#step-2-deploy-the-knowledge-base-stack)
    - [Step 2: Deploy the Hallucination Detection stack _(optional)_](#step-3-deploy-the-hallucination-detection-stack-optional)
    - [Step 3: Deploy the RAG Solution stack](#step-4-deploy-the-rag-solution-stack)
    - [Step 4: Deploy the Conversation Analytics stack _(optional)_](#step-5-deploy-the-conversation-analytics-stack-optional)
    - [Step 5: Set up the Amazon QuickSight dashboard _(optional)_](#step-6-set-up-the-quicksight-dashboard-optional)
    - [Step 6: Automated testing _(optional)_](#step-7-automated-testing-optional)

- [Clean up](#clean-up)
- [Adapt the solution to your use case](#adapt-the-solution-to-your-use-case)
- [Repo Structure](#repo-structure)
- [Contributors](#contributors)

# Overview

### Key Features

- A fast, RAG-based question answering capability that's optimized for  text and voice, and provides a multi-turn user experience that maintains conversational context
- Out-of-the-box [integration with Amazon Connect](https://docs.aws.amazon.com/lexv2/latest/dg/contact-center-connect.html)
- Knowledge Bases for Bedrock integration with [hybrid search](https://aws.amazon.com/about-aws/whats-new/2024/03/knowledge-bases-amazon-bedrock-hybrid-search/) and [metadata filtering](https://aws.amazon.com/about-aws/whats-new/2024/03/knowledge-bases-amazon-bedrock-metadata-filtering/)
- Prompt-based hallucination prevention and LLM guardrails
- Additional hallucination detection using a secondary LLM (optional)
- Fully automated testing (optional)
- Comprehensive conversation analytics dashboard using [Amazon QuickSight](https://aws.amazon.com/quicksight) (optional)
- [Amazon CloudWatch alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html) and alerts (optional)


## Architecture
The following diagram illustrates the solution architecture. The [deployment instructions below](#deploy-and-test-the-solution) will walk you through deploying and testing each of the major subsystems, including the SageMaker notebooks.

<p align="center">
    <img src=images/architecture.png alt="architecture" width="100%">
</p>


# Deploy and test the solution

## *Clone the Repository*

Fork the repository, and clone it to a location of your choice.  For example:

```{bash}
git clone git@github.com:aws-samples/contact-center-genai-agent.git
```

## Prerequisites

You need to have an AWS account and an [AWS Identity and Access Management](https://aws.amazon.com/iam/) (IAM) role and user with permissions to create and manage the necessary resources and components for this application. If you don’t have an AWS account, see [How do I create and activate a new Amazon Web Services account?](https://repost.aws/knowledge-center/create-and-activate-aws-account)

This solution uses [Amazon Bedrock](https://aws.amazon.com/bedrock/) LLMs to find answers to questions from your knowledge base. Before proceeding, if you have not previously done so, request access to at least the following Amazon Bedrock models:

•	Amazon Titan Embeddings G1 – Text
•	Cohere Embed English v3 and Cohere Embed Multilingual v3
•	Anthropic Claude 3 Haiku and Claude 3 Sonnet

If you’ll be integrating with Amazon Connect, make sure you have an instance available in your account. If you don’t already have one, you can [create one](https://aws.amazon.com/connect/). If you plan to deploy the conversation analytics stack, you will need Amazon QuickSight, so make sure you have [enabled it in your AWS account](https://docs.aws.amazon.com/quicksight/latest/user/signing-up.html).


## Deploy the [AWS CloudFormation](https://aws.amazon.com/cloudformation) stacks


### *Step 2: Deploy the Knowledge Base stack*

You will need to start with the Knowledge Base stack first. Either via the AWS CLI or the AWS console, deploy the [infrastructure/bedrock-KB.yaml](./infrastructure/bedrock-KB.yaml) CloudFormation template. You will need to supply the following input parameters:

- A stack name, for example: "**contact-center-kb**".
- The name for an existing S3 bucket, for example: "**contact-center-kb-(your-account-number)**". This is where the content for the demo solution will be stored. _Note: please create this S3 bucket if you don't already have one._
- Do not specify an S3 prefix (future use).
- Choose an embedding model. Recommended: "**amazon.titan-embed-text-v2:0**"
- Choose the "**Fixed-sized chunking**" chunking strategy.
- For the maximum tokens per chunk entry, use **600** for the Titan embedding model. (If you are using the Cohere embedding model, use **512**). This represents about a full page of text.
- For the percentage overlap, use **10** percent.
- Leave the four entries for Index Details at their default values (index name, vector field name, metadata field name, and text field name).

Note that this CloudFormation stack can be used for any Bedrock Knowledge base instance you may need using S3 as a data source.

Choose "Next", and on the **Configure stack options** page choose "Next" again.  On the **Review and create** page, acknowledge the IAM capabilities message and choose "Submit".  The stack will take about 5 minutes to deploy.

### Upload the sample content and test your knowledge base
The demonstration sample for the solution includes an LLM-based "hotel-bot" that can answer questions about the imaginary hotel chain called "Example Corp Hospitality Group". You will need to load the content for this hotel chain into the S3 bucket that was specified for the Knowledge Base stack. 

Either via the AWS CLI or the AWS Management Console, upload the following folders from the [content](./content) section of this repo:

- corporate
- family-getaways
- luxury-suites
- party-times
- seaside-resorts
- waypoint-inns

You can choose either the PDF versions or the Word document versions (Word recommended). When you are done, the top level of your S3 bucket should contain the six folders listed above, each containing a single Word or PDF document.

Next, in the AWS Console, got to Bedrock and select Knowledge bases.  Click on your new knowledge base to open it. You will see a message that "One or more data sources have not been synced."  Select the data source by clicking its radio button, and choose "Sync". The sync process should only take a minute or two.

Once your data source has been synced, you can try some question answering right on the Amazon Bedrock console. 

_**(Note: make sure you have enabled all the models approved by your organization in the Bedrock "Model access" section in the AWS Console.)**_

Select an LLM model, such as Anthropic Claude Haiku, and start asking questions! You may want to peruse the [sample documents](./content/content-pdf) you uploaded for some ideas about questions you may want to ask. 

<p align="center">
    <img src=images/kb-test-example.png alt="kb" width="100%">
</p>

### *Step 3: Deploy the Hallucination Detection stack (optional)*

If want to use the optional asynchronous hallucination detection feature, deploy this stack.  Otherwise move on to the [next section](#step-4-deploy-the-rag-solution-stack).

Note that this CloudFormation stack can be used for any RAG-based solution requiring asynchronous hallucination detection.

Either via the AWS CLI or the AWS console, deploy the [infrastructure/detect-hallucinations.yaml](./infrastructure/detect-hallucinations.yaml) CloudFormation template. You will need to supply the following input parameters:

- A stack name, for example: "**contact-center-hallucination-detection**".
- An LLM to perform the hallucination detection.
    - At the time of writing, there are seven LLMs that are recommended for hallucination detection. For the demo solution, choose the default (**Claude V3 Sonnet**).
- An option to create an [Amazon Key Management Service](https://aws.amazon.com/kms/) (KMS) customer-managed key to encrypt the [Amazon Simple Queue Service](https://aws.amazon.com/sqs/) (SQS) queue and the [Amazon CloudWatch Logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/WhatIsCloudWatchLogs.html) log group for the Lambda function (recommended for production).
- There are two types of CloudWatch alarms in this stack:
    - ERROR alarms, for any code issues with the Lambda function that does the hallucination detection work.
    - WARNING alarms, for when the Lambda function actually detects a hallucination. 
- Both alarm types are optional, but recommended. Choose **yes** to enable or **no** to disable the alarms.
- For the alarms that you enable, you can specify an optional email address or distribution list to receive email notifications about the alarms.

Choose "Next", and on the **Configure stack options** page choose "Next" again.  On the **Review and create** page, acknowledge the IAM capabilities message and choose "Submit".  The stack will take about a minute or two to deploy.

Once the stack has been completed, you can review the resources it creates from the "Resources" tab in the CloudFormation stack. In particular, review the Lambda function code.

If you entered email addresses for the alarm notifications, you should receive email requests asking you to confirm the subscriptions. Confirm them to receive email notifications about any alarms that may occur.


### *Step 4: Deploy the RAG Solution stack*

Next, deploy the [infrastructure/contact-center-RAG-solution.yaml](./infrastructure/contact-center-RAG-solution.yaml) CloudFormation template. 

If you want to integrate with Amazon Connect, make sure you have an instance available in your account. If you don't, you can [create one](https://docs.aws.amazon.com/connect/latest/adminguide/amazon-connect-instances.html).

You will need to supply the following input parameters:

- A stack name, for example: "**contact-center-rag-solution**".
- A name for the Amazon Lex bot, for example, "**hotel-bot**".
- The number of conversation turns to retain for context. This can be optimized for different use cases and data sets. For the hotel bot demo, use the default of 4. 
- An optional ARN for an existing CloudWatch Logs log group for the Lex conversation logs. You will need this if you are planning to deploy the Conversation Analytics stack. _Note: please create this log group if you don't already have one._
- An optional value for [AWS Lambda provisioned concurrency](https://docs.aws.amazon.com/lambda/latest/dg/provisioned-concurrency.html) units for the Lex bot handler function. If set to a non-zero number, this will prevent Lambda cold starts and is recommended for production and for internal testing. For development, 0 or 1 is recommended.
- An option to create a KMS customer-managed key to encrypt the CloudWatch Logs log groups for the Lambda functions (recommended for production).
- If you are integrating with Amazon Connect, provide the Connect instance ARN, as well as the name for a new contact flow that the stack will create for you.
- The knowledge base ID from the Knowledge Base stack you just created. You can easily find this in the "Outputs" tab in the Knowledge Base stack.
- The name of the S3 bucket used by the Knowledge Base stack (also referenced in the "Outputs" tab).
- If you created the Hallucination Detection stack, enter the SQS Queue Name.
- If you opted for a KMS key for your Hallucination Detection stack, enter the KMS Key ARN.

Choose "Next", and on the **Configure stack options** page choose "Next" again.  On the **Review and create** page, acknowledge the IAM capabilities message and choose "Submit".  The stack will take about 5 minutes to deploy.

To try the RAG solution, navigate to the Amazon Lex console and click on the **hotel-bot** Lex bot. The bot has a single language section for the English language. Click on the "Intents" link in the navigation panel to check out the intents for this sample Lex bot. They include the following:

- Intents related to questions about the hotel chain and its various hotel brands: **Accommodations, Amenities, CorporateOverview, Locations, Parking,** etc.
    - These intents are all routed to the RAG solution by Lex.
    - Technically, intents like these could be omitted, allowing the **FallbackIntent** to handle requests of this nature. However, including these intents (and their sample utterances) provides Lex with information about the "language" of your solution domain, allowing it to better optimize its speech-to-text engine and improve speech transcription accuracy.
    - In addition, including these intents is useful for conversation analytics, as we shall see later.
- **SwitchBrand**: an intent designed to improve conversation flow, by allowing the user to say things like "what about at your other hotels?" in the middle of a conversation.
- **Booking**: demonstrates an example of routing the caller to a live agent queue.
- **SpeakToAgent**: for when a caller specifically requests a live agent.
- **Welcome, Help, and Goodbye**: conversation support intents to start and end the conversation, or ask what the bot can do.
- **FallbackIntent**: the standard Lex intent for questions or requests that don't match any other intent.
    - In this example, such requests are also routed to the RAG solution to allow the LLM to answer.
- **SelectKnowledgeBase and SelectLLM**: allow the user to direct the RAG Solution to use a a different Knowledge Base instance (if more than one is available), or to use a different LLM.
    - *Note: these intents are designed for testing purposes, and should normally be included only in non-production deployments.*
    - *Note: You can test the RAG Solution with any of the LLMs available on Bedrock.*
    - *Note: You can switch to a different knowledge base or LLM mid-conversation, if desired.*
- **ToggleLLMGuardrails and ToggleLLMContext**: allow the user to turn the prompt-based LLM guardrails off or on, and to disable or enable the retrieval of information from the knowledge base.
    - *Note: these intents are designed for testing purposes, and should normally be included only in non-production environments.*
    - *Note: You can toggle these settings mid-conversation, if desired.*

You can click the "Test" button in the Lex console to try the solution.

<p align="center">
    <img src=images/lex-test-example.png alt="lex" width="100%">
</p>


Try some sample conversations, for example:
- Ask "we're looking for a nice place for a family vacation" and the bot will respond  _"Example Corp Family Getaways offers family-friendly accommodations..."_
- Ask "where are they located?" and the bot will respond _"Example Corp Family Getaways has locations in..."_
- Ask "tell me more about the one in pigeon forge" and the bot will respond _"The Example Corp Family Getaways resort in Pigeon Forge, Tennessee is..."_

You can refer to the [sample documents](./content/content-pdf) you uploaded for some ideas about questions to ask.

If you deployed the Hallucination Detection stack, you can take a look at its assessment of the answers you got when you tested. From the Hallucination Detection stack CloudFormation stack, in the "Resouces" tab click on the **LambdaFunctionLogGroup** entry. This will open the CloudWatch Logs log group for the Lambda hallucination detection function. You can inspect the log statements to observe the hallucination detection process in action:

<p align="center">
    <img src=images/hallucination-detection-example.png alt="hallucinations" width="100%">
</p>

If you're integrating with Amazon Connect, there will be a new contact flow in the Amazon Connect instance you specified, as shown in the following screenshot.

<p align="center">
    <img src=images/connect-sample-flow.png alt="sample-flow" width="100%">
</p>

To test using voice, just claim a phone number, associate it with this contact flow, and give it a call.


### *Step 5: Deploy the Conversation Analytics stack (optional)*

To enable the Conversation Analytics component, first deploy the [infrastructure/lex-data-pipeline.yaml](./infrastructure/lex-data-pipeline.yaml) CloudFormation template. 

_**Note: make sure you have already [enabled Amazon QuickSight in your AWS account](https://docs.aws.amazon.com/quicksight/latest/user/signing-up.html) before deploying this stack.**_

You'll need to supply the following input parameters:

- A stack name, for example: "**contact-center-rag-analytics**".
- The name of the Lex conversation logs log group.
    - _You can find this in the "Output" section of the RAG Solution CloudFormation stack._
- Select an option for purging source log streams from the log group.
    - _For testing, select "no"._
- Select an option for redacting sensitive data using from the conversation logs.
    - _For testing, select "no"._
- Select an option for allowing unredacted logs for the Lambda function in the data pipeline.
    - _For testing, select "yes"._
- Leave the PII entity types and confidence score thresholds at their default values.
- Select an option for creating a KMS customer managed key (CMK). If you create a CMK, it will be used to encrypt the data in the S3 bucket that this stack will create where the "normalized" conversation data will be housed. This allows you to control which IAM principals are allowed to decrypt the data to view it. This setting is recommended for production.
- Select the options for enabling CloudWatch alarms for ERRORS and WARNINGS in the Lex data pipeline.
    - _It is recommended to enable these alarms._

Choose "Next", and on the **Configure stack options** page choose "Next" again.  On the **Review and create** page, acknowledge the IAM capabilities message and choose "Submit".  The stack should only take a minute or two to deploy.

The following diagram illustrates the architecture of this stack.

<p align="center">
    <img src=images/lex-data-pipeline.png alt="data-pipeline" width="80%">
</p>

As Amazon Lex writes conversation log entries to CloudWatch Logs, they are picked up by [Amazon Data Firehose](https://aws.amazon.com/firehose) and streamed to an S3 bucket. Along the way, a Lambda transformation function simplifies the JSON structure of the data to make it more user-friendly for querying purposes. The Lambda function can also redact sensitive data using [Amazon Comprehend](https://aws.amazon.com/comprehend), and optionally purge the entries from the CloudWatch Logs log group as it consumes them.

On a scheduled basis (every 5 minutes), an [AWS Glue](https://aws.amazon.com/glue) crawler inspects any new data in the S3 bucket, and updates a data schema that is used by [Amazon Athena](https://aws.amazon.com/athena) to provide a SQL interface to the data. This allows tools like Amazon QuickSight to create near realtime dashboards, analytics, and visualizations of the data.

### *Step 6: Set up the QuickSight dashboard (optional)*

_**Note: before you create the QuickSight dashboard, make sure to return to the Amazon Lex console and ask a few questions, in order to generate some data for the dashboard.  It will take about five minutes for the pipeline to process this new conversation logs data and make it available to QuickSight.**_

To set up dashboards and visualizations in QuickSight, go to QuickSight in the AWS Console, click on the configuration icon, and choose "Manage QuickSight".  

![alt text](<images/quicksight-config-icon.png>)

Under "Security & permissions", choose the "Manage" button in the "QuickSight access to AWS services" section. Under the "Amazon S3" item, choose "Select S3 buckets".  Enable access to the S3 bucket created by the Conversation Analytics stack in Step 5 (it will have a name with a 12-character unique identifier prepended to "lex-conversation-logs"). You don't need to enable write permissions.

Choose "Finish", and then choose "Save". 

Next, click on the QuickSight menu icon to return to the main view in QuickSight.

<p align="left">
    <img src=images/quicksight-menu.png alt="quicksight-menu" width="10%">
</p>

In the navigation menu, choose "Datasets" and then choose "New dataset". From the list of dataset sources, choose "Athena". Enter a data source name (for example **"contact-center-rag-analytics"**) and choose "Create data source".

In the "Choose your table" window, select your Database in the dropdown menu, then select the radio button for your "lex_conversation_logs" table, and choose "Edit/Preview data".

<p align="center">
    <img src=images/quicksight-select-database-table.png alt="quicksight-table" width="30%">
</p>

This will open your new QuickSight dataset. You can review the various attributes available, and see some results from your testing.

<p align="center">
    <img src=images/quicksight-dataset.png alt="quicksight-dataset" width="100%">
</p>

For improved speed in displaying the data, you can select the "SPICE" option for Query mode, but that will mean you will need to refresh SPICE (or set up an hourly auto-update schedule) when you want to see any data updates based on additional testing. So for now, leave the setting on "Direct query".

When you are ready, choose the "PUBLISH & VISUALIZE" button at the top right in the window.  In the "New sheet" window, keep the defaults and choose "CREATE". This will open the analysis page, where you can start creating visualizations.

<p align="center">
    <img src=images/quicksight-analysis-example.png alt="quicksight-analysis" width="100%">
</p>

### *Step 7: Automated testing notebooks (optional)*

To try the automated testing capability, you will need a SageMaker Jupyter notebook (or, you can run the notebooks locally in your IDE or other environment that supports Jupyter notebooks).

In the SageMaker console, scroll the navigation pane to "Notebook" and select "Notebook instances".  Then choose "Create notebook instance".

Give your notebook a name, such as "**contact-center-rag-testing**".

In order to enable multi-threaded testing, it is recommended to select a larger instance, such as **ml.m5.2xlarge** (which has 8 vCPUs) or **ml.m5.4xlarge** (which has 16 vCPUs). Don't forget to stop them when they're not in use! 

Take the default setting for "Platform identifier", e.g., "Amazon Linux 2, Jupyter Lab 3". 

Under "Additional configuration", increase the "Volume size in GB" setting to 50 GB.

In the "Permissions and encryption" section, under "IAM role", choose "Create a new role" in the dropdown menu. In the "Create an IAM role" window, you can specify any specific S3 buckets you want to provide access to (none are needed for this solution). 

<p align="center">
    <img src=images/sagemaker-create-role.png alt="sagemaker-role" width="50%">
</p>

Choose "Create role", and then choose "Create notebook instance". It will take several minutes for your notebook instance to become available. While it is being created, we can update the IAM role to add some inline policies we will need for accessing Bedrock and Lex.

On the Notebook instances page, click the link for you notebook instance (e.g., "contact-center-rag-testing") and then click the "IAM role ARN" to open the role. Add the following four inline policies:

- [bedrock-agents-retrieve.json](notebooks/iam-roles/bedrock-agents-retrieve.json)
- [bedrock-invoke-model-all.json](notebooks/iam-roles/bedrock-invoke-model-all.json)
- [lex-invoke-bot.json](notebooks/iam-roles/lex-invoke-bot.json)
- [opensearch-serverless-api-access.json](notebooks/iam-roles/opensearch-serverless-api-access.json)

You can revise these roles to limit resource access as needed.

Once your notebook instance has started, choose "Open Jupyter" to open the notebook. Upload the following files to your notebook instance:

- [bedrock_helpers.py](notebooks/bedrock_helpers.py) - configures LLM instances for the notebooks
- [bedrock_utils](notebooks/bedrock_utils) - _Note: make sure to upload all subfolders and files, and ensure that the folder structure is correct._
- [run_tests.ipynb](notebooks/run_tests.ipynb) - Runs a set of test cases
- [generate_ground_truths.ipynb](notebooks/generate_ground_truths.ipynb) - Given a set of questions, generate potential ground truth answers.
- [test-runs](test/test-runs/) - _Note: this folder should contain Excel workbooks_

Open the "**run_tests.ipynb**" notebook. In the first cell, you will need to replace the "bot_id" and "bot_alias_id" with the values for your Lex bot (you can find these in the "Output" tab in the RAG Solution stack you created in Step 4). Once you've updated these values, choose "Restart & Run All" from the "Kernel" menu.

If you are using a ml.m5.2xlarge instance type, it should take about a minute to run the 50 test cases in the [test-runs/test-cases-claude-haiku-2024-09-02.xlsx](test/test-runs/test-cases-claude-haiku-2024-09-02.xlsx) workbook. When complete, you should find a corresponding "test-results" workbook in the test-runs folder in your notebook.

<p align="center">
    <img src=images/sample-test-results.png alt="sample-test-results" width="100%">
</p>

After a few minutes, you will also be able to see the test results in your Conversation Analytics dashboard.

<p align="center">
    <img src=images/quicksight-test-run.png alt="quicksight-test-run" width="100%">
</p>

## Adapt the solution to your use case
This solution can be adapted to your specific use cases with minimal work.
1. *Replace the Knowledge Bases for Bedrock content with your content.* Replace the content in the S3 bucket from Step 1 above, and organize it into a folder structure that makes sense for your use case.
2. *Replace the intents in the Amazon Lex bot with intents for your use case.* Modify the Lex bot definition from Step 3 above to reflect the interactions you want to enable for your use cases.
3. *Modify the LLM prompts in the [bedrock_utils](src/lex/hotel-bot-handler/bedrock_utils/hotel_agents) code.* In the Lex bot fulfillment Lambda function, review the LLM prompt definitions in the bedrock_utils folder. For example, provide a use case specific definition for the role of the LLM based agent.
4. *Modify the [bot handler](src/lex/hotel-bot-handler/TopicIntentHandler.py) code if necessary.* In the Lex bot fulfillment Lambda function, review the code in the TopicIntentHandler function. For the Knowledge Base search, this code provides an example that uses the sample hotel brands as topics. You can replace this metadata search query with one appropriate for your use cases.

## Clean up
When you no longer need the solution deployed in your AWS account, you can simply delete the four CloudFormation stacks, and the SageMaker notebook instance if you created one.

---

# Repo Structure

- [content](content) - Sample documents for the hotel chain example (sample files not meant to be readable/editable)
    - [content/content-pdf](content/content-pdf) - PDF versions 
    - [content/content-word](content/content-word) - MS Word versions 
- [docs](docs) - Solution documentation (sample files not meant to be readable/editable)
- [images](images) - README images
- [infrastructure](infrastructure) - CloudFormation templates
- [notebooks](notebooks) - SageMaker Jupyter notebooks for testing
- [src](src) - Python source code
    - [src/connect](src/connect) - Custom resource to add a contact flow into a Connect instance
    - [src/hallucinations](src/hallucinations) - Lambda code to perform hallucination detection
    - [src/lex](src/lex) - Lambda handler for Lex, and Lambda layer with latest boto3 libraries
    - [src/lex/hotel-bot-handler/bedrock_utils](src/lex/hotel-bot-handler/bedrock_utils) - Helpful Bedrock utility functions
        - [models](src/lex/hotel-bot-handler/bedrock_utils/models) - Wrapper classes for LLMs
        - [conversational_agents](src/lex/hotel-bot-handler/bedrock_utils/conversational_agents) - Generic RAG implementation classes and prompts
        - [hotel_agents](src/lex/hotel-bot-handler/bedrock_utils/hotel_agents) - Subclassed versions of conversational_agents for the Example Corp Hospitality Group example
        - [knowledge_base.py](src/lex/hotel-bot-handler/bedrock_utils/knowledge_base.py) - Wrapper class for Knowledge Bases for Bedrock
    - [src/opensearch](src/opensearch) - Custom resource to create an index in an OpenSearch Serverless collection
- [test/test-runs](test/test-runs) - Test runs

## Contributors

- [Brian Yost](https://phonetool.amazon.com/users/bryost), Principal Deep Learning Architect, AWS Generative AI Innovation Center
- [Alvaro Sanchez Martin](https://phonetool.amazon.com/users/marzalv), Senior Solutions Architect, ISV

