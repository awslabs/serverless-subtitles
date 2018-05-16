import boto3


def handler(event, context):
    fileUUID = event.get("fileUUID")
    transcribe = boto3.client("transcribe")

    response = transcribe.get_transcription_job(TranscriptionJobName=fileUUID)
    status = response.get("TranscriptionJob").get("TranscriptionJobStatus")

    print("Status for job " + fileUUID + " is " + status)
    event["status"] = status

    return event
