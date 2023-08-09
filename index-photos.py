import json
import boto3
import base64
#import requests
import logging
from datetime import datetime

# Configure the root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        # Extract relevant information from the S3 PUT event
        print('testing codebuild')
        s3_event = event['Records'][0]['s3']
        bucket_name = s3_event['bucket']['name']
        object_key = s3_event['object']['key']
        
        # Get S3 object metadata to retrieve custom labels
        s3_client = boto3.client('s3')
        s3_object_metadata = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        
        print(s3_object_metadata)
        if 'x-amz-meta-customlabels' in s3_object_metadata['Metadata']:
            custom_labels = s3_object_metadata['Metadata']['x-amz-meta-customlabels'].split(',')
        else:
            custom_labels = []

        
        print(custom_labels)
        #Detect labels in the image using Rekognition
        rekognition_client = boto3.client('rekognition')
        
        response = rekognition_client.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': object_key
                }
            },
            MaxLabels =10
        )
        
        
        # Extract the detected labels from Rekognition response
        detected_labels = []
        for label in response['Labels']:
            detected_labels.append(label['Name'].lower())
        
        # Combine custom labels and detected labels
        all_labels = custom_labels + detected_labels
        unique_labels = list(set(all_labels))
        
        
        print(unique_labels)
        # Create the JSON object to be indexed in Elasticsearch
        timestamp = datetime.now().isoformat()
        json_object = {
            'objectKey': object_key,
            'bucket': bucket_name,
            'createdTimestamp': timestamp,
            'labels': unique_labels
        }

        # Log the information
        logger.info(f"Received S3 PUT event for object: {object_key}")
        logger.info(f"Detected labels: {detected_labels}")
        logger.info(f"Custom labels: {custom_labels}")
        logger.info(f"Unique labels: {unique_labels}")
        
        # Index the JSON object in Elasticsearch
        es_endpoint = 'https://search-photos-wavsad5xftkjpo2dx7cdtng7ou.us-east-1.es.amazonaws.com' 
        index_url = f"{es_endpoint}/newphotos/_doc/"
       
        headers = {"Content-Type": "application/json"}
        
        print(json.dumps(json_object).encode("utf-8"))
        response = requests.post(index_url, data=json.dumps(json_object).encode("utf-8"), headers=headers, auth=('mzahid', 'Lahore11!'))
        response.raise_for_status()  # Raise an exception for non-2xx responses
        
        # Log the indexing result
        logger.info(f"Indexing response: {response.text}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(json_object)
        }
    except Exception as e:
        # Log the error and return an error response
        logger.exception("An error occurred during execution")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
