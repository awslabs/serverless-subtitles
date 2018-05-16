import unittest
import json
import pprint
from index import makeVTTFile, translate


class TranslateTests(unittest.TestCase):

    def test_makewebVTT(self):
        data = json.load(open('test/asrOutput.json'))
        items = data.get("results").get("items")

        transcripts = makeVTTFile(items)
        translations = translate(transcripts, "en", "fr")
        self.assertEqual(len(transcripts), len(translations))
