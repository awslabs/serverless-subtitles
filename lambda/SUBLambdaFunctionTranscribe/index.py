import boto3


def handler(event, context):

    transcribe = boto3.client('transcribe')
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('subtitles')

    bucket = event.get("bucket")
    fileUUID = event.get("fileUUID")
    mediaFileUri = bucket + "/2-transcoded/" + fileUUID + ".mp3"

    print("Start the transcription job : " + mediaFileUri)
    transcribe.start_transcription_job(
        TranscriptionJobName=fileUUID,
        LanguageCode='en-US',
        MediaFormat='mp3',
        Media={'MediaFileUri': "https://s3.amazonaws.com/" + mediaFileUri}
    )

    print("Update the state")
    table.update_item(
        ExpressionAttributeNames={'#S': 'State'},
        ExpressionAttributeValues={':s': 'TRANSCRIBING'},
        Key={'Id': fileUUID},
        TableName='subtitles',
        UpdateExpression='SET #S = :s'
    )

    return event
