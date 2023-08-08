import json
import logging
import requests
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ES_HOST = "https://search-photos-wavsad5xftkjpo2dx7cdtng7ou.us-east-1.es.amazonaws.com/newphotos/_doc/"
REGION = 'us-east-1'

client = boto3.client('lexv2-runtime')
def lambda_handler(event, context):
    try:
        query = event['q']
        print("event: ",event)
        
    
        response = client.recognize_text(
            botId='OUIXAJUGMS',        
            botAliasId='KXQ3POK2DQ',   
            localeId='en_US',         
            sessionId='testuser',     
            text=query 
        )
        
        print("Lex Response:", json.dumps(response, indent=2)) 
        
        labels = []
        print(response)
        slots = response['sessionState']['intent']['slots']
        
        if slots:
            labels = [value for value in slots.values() if value]
        
        if not labels:
            logger.info("No photo collection for query: {}".format(query))
            return {'statusCode': 200, 'data': []}
        
        img_paths = get_photo_paths(labels)
        return {'statusCode': 200, 'data': img_paths}
    
    except Exception as e:
        logger.exception("An error occurred during execution ")
        return {'statusCode': 500, 'data': str(e)}

def get_photo_paths(labels):
    unique_labels = list(set(labels))
    img_paths = []
    
    for label in unique_labels:
        path = ES_HOST + '/_search?q=labels:' + label
        response = requests.get(path, headers={"Content-Type": "application/json"}, auth=('mzahid', 'Lahore11!'))
        
        if response.status_code == 200:
            data = response.json()
            hits = data.get('hits', {}).get('hits', [])
            for hit in hits:
                img_bucket = hit["_source"].get("bucket")
                img_name = hit["_source"].get("objectKey")
                if img_bucket and img_name:
                    img_link = f'https://{img_bucket}.s3.amazonaws.com/{img_name}'
                    img_paths.append(img_link)
        else:
            logger.error("Elasticsearch search failed with status code: {}".format(response.status_code))
    
    return img_paths