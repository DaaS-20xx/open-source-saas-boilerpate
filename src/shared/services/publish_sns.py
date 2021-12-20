import boto3, os, json, traceback
from uuid import UUID
import datetime
from json import JSONEncoder


class DateTimeUUIDEncoder(JSONEncoder):
    #Override the default method
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime, datetime.time)):
            return obj.isoformat()
        elif isinstance(obj, UUID):
            return obj.hex
        return json.JSONEncoder.default(self, obj)

def publish_to_sns(Message, userid):
    topicArn = os.environ.get('AWS_SNS_ARN')
    snsClient = boto3.client(
        'sns',
        aws_access_key_id='aws_access_key_id',
        aws_secret_access_key='aws_secret_access_key',
        region_name='eu-central-1'
    )
    
    message_json = json.dumps(Message, cls=DateTimeUUIDEncoder)
    print(topicArn)
    try:
        response = snsClient.publish(TopicArn=topicArn,
                                    Message=message_json,
                                    Subject='PaymentSuccess',
                                    MessageGroupId=userid,
                                    MessageAttributes={"TransactionType":{"DataType":"String", "StringValue":"PaymentSyuccess"}}
                                    )
        
        print(response['ResponseMetadata']['HTTPStatusCode'])
        print(response)
    except Exception as ex:
        stacktrace = traceback.format_exc()
        print(stacktrace)