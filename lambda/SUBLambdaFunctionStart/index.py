import boto3
import uuid
import json
import datetime

def handler(event, context):
    stepFunctions = boto3.client('stepfunctions')
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('subtitles')
    s3 = boto3.client("s3")

    fileUUID = str(uuid.uuid4())
    filename = event.get("Records")[0].get("s3").get("object").get("key")
    bucket = event.get("Records")[0].get("s3").get("bucket").get("name")

    print("Verifying file type")
    if filename[-4:] != ".mp4":
        s3.delete_object(
            Bucket=bucket,
            Key=filename
        )

    print("Initialize item in Dynamodb with id " + fileUUID)
    item = {
       'Id': fileUUID,
       'FileKey': filename.replace("0-input/", ""),
       'State': "ORIGINAL",
       'Created': datetime.datetime.now().isoformat()
    }
    table.put_item(TableName='subtitles', Item=item)

    print(
        "Move the file "+bucket+"/"+filename+" to its file UUID name : " +
        bucket + "/1-source/"+fileUUID+".mp4"
    )
    response = s3.copy_object(
        Bucket=bucket,
        Key="1-source/"+fileUUID+".mp4",
        CopySource={
            "Bucket": bucket,
            "Key": filename
        }
    )
    s3.delete_object(Bucket=bucket, Key=filename)

    print("Start state machine")
    response = stepFunctions.list_state_machines()
    stateMachineArn = False
    for sm in response.get("stateMachines"):
        if sm.get("name") == "Subtitles":
            stateMachineArn = sm.get("stateMachineArn")

    response = stepFunctions.start_execution(
        stateMachineArn=stateMachineArn,
        name=fileUUID,
        input=json.dumps({
            "fileUUID": fileUUID,
            "bucket": bucket
        })
    )

    print("State Machine has started")
    return True
