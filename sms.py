import boto3

# Create an SNS client
client = boto3.client(
    "sns",
    aws_access_key_id="AKIA2UF2ZTTJZYIUUE6P",
    aws_secret_access_key="N02WXtRjgco64oOYTPfHa7PIvre8hUKkCepyul1u",
    region_name="ap-southeast-2"
)

# Send your sms message.
client.publish(
    PhoneNumber="+61423861767",
    Message="From Python",
    MessageAttributes={
        'AWS.SNS.SMS.SenderID': {
        'DataType': 'String',
        'StringValue': 'ABFTech'
        }
    }
)
