import boto3


def handler(event, context):
    fileUUID = event.get("fileUUID")
    bucket = event.get("bucket")

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('subtitles')
    transcoder = boto3.client('elastictranscoder')
    iam = boto3.client('iam')

    print("Start a job in transcoder")
    response = transcoder.list_pipelines()
    pipelineId = False
    for p in response.get("Pipelines"):
        if p.get("InputBucket") == bucket:
            pipelineId = p.get("Id")

    if pipelineId is False:
        print("Pipeline is not created, we create it")
        response = iam.get_role(RoleName="SubtitleElasticTranscoder")
        roleArn = response.get("Role").get("Arn")

        response = transcoder.create_pipeline(
            Name="Subtitles",
            InputBucket=bucket,
            OutputBucket=bucket,
            Role=roleArn,
        )
        pipelineId = response.get("Pipeline").get("Id")

    transcoder.create_job(
        PipelineId=pipelineId,
        Input={'Key': '1-source/'+fileUUID+'.mp4'},
        Output={
            'Key': '2-transcoded/'+fileUUID+'.mp3',
            'PresetId': '1351620000001-300010'
        }
    )
    print("Job has been created in the pipeline")

    table.update_item(
        ExpressionAttributeNames={'#S': 'State'},
        ExpressionAttributeValues={':s': 'TRANSCODED'},
        Key={'Id': fileUUID},
        TableName='subtitles',
        UpdateExpression='SET #S = :s'
    )

    print("State has been updated")

    return event
