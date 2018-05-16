import boto3
import urllib2
import json
import re
from datetime import timedelta


def callJobTranscription(event):
    transcribe = boto3.client("transcribe")

    print("Call the job to download transcription")
    fileUUID = event.get("fileUUID")
    response = transcribe.get_transcription_job(TranscriptionJobName=fileUUID)
    transcriptFileUri = response.get("TranscriptionJob") \
        .get("Transcript").get("TranscriptFileUri")
    req = urllib2.Request(transcriptFileUri)
    opener = urllib2.build_opener()
    f = opener.open(req)
    data = json.loads(f.read())
    return data.get("results").get("items")


def makeVTTFile(items):
    print("Make a WebVTT file")
    limit = 2.5
    startingCaption = 0
    transcripts = []
    wasPunctuation = False
    for j, item in enumerate(items):

        # If elemenr is a punctuation, we just add it to the last transcript
        # element
        if item.get("type") == "punctuation":
            transcripts[-1] = transcripts[-1] + \
                item.get("alternatives")[0].get("content")
            wasPunctuation = True
        else:
            # As the translate service may send back many alternatives, we
            # should select the right one
            index = 0
            for i, alternative in enumerate(item.get("alternatives")):
                if item.get("alternatives")[index].get("confidence") > \
                        alternative.get("confidence"):
                    index = i

            # We set the start time and the start string as refered in the VTT
            # specification
            start_time = float(item.get("start_time"))
            start_string = str(timedelta(seconds=start_time))[:-3]

            # If the transcripts array is empty, we must initiate it with
            # the first timestamp header
            # If the current start time is higher than the window limit, we
            # should start a new caption header
            if len(transcripts) == 0 or \
                    float(start_time) >= float(startingCaption) + limit or \
                    wasPunctuation:
                end_time = float(item.get("start_time")) + limit
                end_string = str(timedelta(seconds=end_time))[:-3]

                # Insert a new caption and copy it in the translated
                # transcripts
                caption = "\n\n" + start_string + " --> " + end_string + "\n"
                transcripts.append(caption)

                # We mark a blank line for transcripts on order to correctly
                # process translation afterwards
                transcripts.append("")

                # We reset the start time for the caption and the punctuation
                # flag
                startingCaption = start_time
                wasPunctuation = False

            # If we already write in the last element of the transcript then
            # we use the " " separator
            separator = " "
            if not transcripts[-1]:
                separator = ""

            # Finally we had the alternative content
            transcripts[-1] = transcripts[-1] + separator + \
                item.get("alternatives")[index].get("content")

    return transcripts


def translate(transcripts, sourceLanguage, targetLanguage):
    translate = boto3.client('translate')

    temp = ""
    charLimit = 10000
    delimiter = " < "
    translatedTranscripts = [""] * len(transcripts)
    tempBuckets = []

    print("Create temporary translation buckets for translation char limit")
    for i, transcript in enumerate(transcripts):
        if re.search(".*(-->).*", transcript):
            # Skip the timestamp information and copy it in the target array
            translatedTranscripts[i] = transcript
        else:
            if len(temp) + len(transcript) >= charLimit or\
                    i == len(transcripts) - 1:
                # If we go throught the car limit or this is the last temp
                # bucket
                temp = temp + transcript
                tempBuckets.append(temp)
                temp = ""
            else:
                temp = temp + transcript + " " + delimiter + " "

    print("Translating " + str(len(tempBuckets)) + " temporary buckets")

    # The index is starting at 1 as 0 is for the timestamp data
    translatedIndex = 1
    for j, tempBucket in enumerate(tempBuckets):
        print(
            "Temp bucket #" + str(j) + " with " +
            str(len(tempBucket)) + " characters"
        )

        response = translate.translate_text(
            Text=tempBucket,
            SourceLanguageCode=sourceLanguage,
            TargetLanguageCode=targetLanguage
        )
        translatedText = response.get("TranslatedText")

        print(
            "Translation #" + str(j) + " with " +
            str(len(translatedText)) + " characters"
        )
        translatedArray = translatedText.split(delimiter)

        for k, translatedItem in enumerate(translatedArray):
            translatedTranscripts[translatedIndex + 2*k] = translatedItem

        translatedIndex = translatedIndex + 2*len(translatedArray)

    # For debug purpose, uncomment the following
    # for l, transcript in enumerate(transcripts):
    #     if not re.search(".*(-->).*", transcript):
    #         print(
    #             "Index " + str((l-1)/2) + "\n"
    #             "Original version   : " + transcript + "\n" +
    #             "Translated version : " + translatedTranscripts[l] + "\n\n"
    #         )

    return translatedTranscripts


def storeInS3(bucket, transcripts, fileUUID, languageCode):
    print("Store result in s3")
    s3 = boto3.client('s3')
    webVTTTranscript = "WEBVTT\n" + "".join(transcripts)
    s3.put_object(
        Body=webVTTTranscript,
        Bucket=bucket,
        Key='4-translated/' + fileUUID + '.' + languageCode + '.vtt'
    )


def updateDynamo(fileUUID):
    print("Update the dynamodb table")
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('subtitles')

    table.update_item(
        ExpressionAttributeNames={"#S": 'State'},
        ExpressionAttributeValues={':s': 'TRANSLATED'},
        Key={'Id': fileUUID},
        TableName='subtitles',
        UpdateExpression='SET #S = :s'
    )


def handler(event, context):
    fileUUID = event.get("fileUUID")
    bucket = event.get("bucket")
    sourceLanguage = 'en'
    targetLanguages = [
        "ar",
        "es",
        "fr",
        "de",
        # "pt",
        "zh"
    ]

    items = callJobTranscription(event)

    transcripts = makeVTTFile(items)
    storeInS3(bucket, transcripts, fileUUID, sourceLanguage)

    for i, language in enumerate(targetLanguages):
        translatedTranscripts = translate(
            transcripts,
            sourceLanguage,
            language
        )

        storeInS3(bucket, translatedTranscripts, fileUUID, language)

    return event
