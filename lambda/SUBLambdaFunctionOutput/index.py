import boto3
import re


def move_object(sourceBucket, sourceKey, destinationBucket,
                destinationKey, isVTT):
    s3 = boto3.client("s3")
    print(
        "Move " + sourceBucket + "/" + sourceKey + " to " +
        destinationBucket + "/" + destinationKey
    )
    if isVTT is True:
        s3.copy_object(
            Bucket=destinationBucket,
            Key=destinationKey,
            CopySource=sourceBucket + sourceKey,
            ContentType="text/vtt",
            MetadataDirective="REPLACE"
        )
    else:
        s3.copy_object(
            Bucket=destinationBucket,
            Key=destinationKey,
            CopySource=sourceBucket + sourceKey
        )

    s3.delete_object(
        Bucket=sourceBucket,
        Key=sourceKey
    )


def handler(event, context):
    s3 = boto3.client("s3")
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('subtitles')
    sourceLanguage = 'en'
    targetLanguages = [
        "ar",
        "es",
        "fr",
        "de",
        # "pt",
        "zh"
    ]

    fileUUID = event.get("fileUUID")
    mediaBucket = event.get("bucket")

    print("Working with file UUID " + fileUUID + " from bucket " + mediaBucket)

    # Identify static bucket
    staticBucket = ""
    buckets = s3.list_buckets()
    for b in buckets.get("Buckets"):
        isStaticBucket = re.search(
            "subtitle\\.static\\.(.*)\\.aws\\.com",
            b.get("Name")
        )
        if isStaticBucket:
            staticBucket = "subtitle.static." + isStaticBucket.group(1) + \
                ".aws.com"
    print("Target bucket is : " + staticBucket)

    directory = "files/" + fileUUID + "/"

    move_object(
        mediaBucket,
        "/1-source/" + fileUUID + ".mp4",
        staticBucket,
        directory + fileUUID + ".mp4",
        False
    )

    move_object(
        mediaBucket,
        "/4-translated/" + fileUUID + "." + sourceLanguage + ".vtt",
        staticBucket,
        directory + fileUUID + ".en.vtt",
        True
    )

    for i, targetLanguage in enumerate(targetLanguages):
        move_object(
            mediaBucket,
            "/4-translated/" + fileUUID + "." + targetLanguage + ".vtt",
            staticBucket,
            directory + fileUUID + "." + targetLanguage + ".vtt",
            True
        )

    print("Clean mp3 files from 2-transcoded")
    s3.delete_object(
        Bucket=mediaBucket,
        Key="2-transcoded/"+fileUUID+".mp3"
    )

    print("Update Dynamodb")
    table.update_item(
        ExpressionAttributeNames={'#S': 'State'},
        ExpressionAttributeValues={':s': 'DONE'},
        Key={'Id': fileUUID},
        TableName='subtitles',
        UpdateExpression='SET #S = :s'
    )

    return True
