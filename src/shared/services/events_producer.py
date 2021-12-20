import boto3, os, json
from uuid import UUID
import datetime
from json import JSONEncoder

aws_sqs_url = os.environ.get('AWS_SQS_QUEUE_URL')
aws_sqs_name = os.environ.get('AWS_SQS_QUEUE_NAME')
    
class DateTimeUUIDEncoder(JSONEncoder):
    #Override the default method
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime, datetime.time)):
            return obj.isoformat()
        elif isinstance(obj, UUID):
            return obj.hex
        return json.JSONEncoder.default(self, obj)

def send_to_sqs_queue(Message, userid):
    print("stripe objet received")
    print(Message)
    sqs_client = boto3.client("sqs", region_name = "eu-central-1",
        aws_access_key_id='AKIAVJNCNQJFMBKHSVG7',
        aws_secret_access_key='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'
    )
    
    print("convert message to JSON")
    message_json = json.dumps(Message, cls=DateTimeUUIDEncoder)
    print(message_json)
    response = sqs_client.send_message(QueueUrl = aws_sqs_url, MessageBody=message_json, MessageGroupId =userid)
    print("****response from sqs****")
    print(response)
    return response