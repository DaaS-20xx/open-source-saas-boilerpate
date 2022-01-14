import sys
from sys import stdout
import boto3, os, json, traceback
from uuid import UUID
import datetime
from json import JSONEncoder

class CustomJSONEncoder(JSONEncoder):
    #Override the default method
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime, datetime.time)):
            return obj.isoformat()
        elif isinstance(obj, UUID):
            return obj.hex
        return JSONEncoder.default(self, obj)

def publish_to_sns(Message, userid):
    topicArn = os.environ.get('AWS_SNS_ARN')
    snsClient = boto3.client(
        'sns',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name='eu-central-1'
    )
    message_json = json.dumps({'user_id':str(Message.id), 'user_email':Message.email, 'user_name':Message.username, 'user_status':'new'})
    #message_json = json.dumps(Message, cls=CustomJSONEncoder)
    print(message_json, file=sys.stdout)
    print(topicArn, file=sys.stdout)
    try:
        response = snsClient.publish(TopicArn=topicArn,
                                    Message=message_json,
                                    Subject='UserRegistered',
                                    MessageAttributes={"TransactionType":{"DataType":"String", "StringValue":"UserRegistered"}}
                                    )
        
        print(response['ResponseMetadata']['HTTPStatusCode'], file=sys.stdout)
        print(response, file=sys.stdout)
    except Exception as ex:
        stacktrace = traceback.format_exc()
        print(stacktrace, file=sys.stdout)
        sys.stdout.flush()