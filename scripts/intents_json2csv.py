"""
Copyright 2018 IBM Corporation
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import argparse
import json
import logging
import os
import sys

from wawCommons import getScriptLogger, openFile, setLoggerConfig, toIntentName

logger = getScriptLogger(__file__)

def main(argv):
    parser = argparse.ArgumentParser(description='Decompose Bluemix conversation service intents in .json format to intent files in .csv format', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # positional arguments
    parser.add_argument('intents', help='file with intents in .json format')
    parser.add_argument('intentsDir', help='directory with intents files')
    # optional arguments
    parser.add_argument('-ni', '--common_intents_nameCheck', action='append', nargs=2, help="regex and replacement for intent name check, e.g. '-' '_' for to replace hyphens for underscores or '$special' '\\L' for lowercase")
    parser.add_argument('-s', '--soft', required=False, help='soft name policy - change intents and entities names without error.', action='store_true', default="")
    parser.add_argument('-v', '--verbose', required=False, help='verbosity', action='store_true')
    parser.add_argument('--log', type=str.upper, default=None, choices=list(logging._levelToName.values()))
    args = parser.parse_args(argv)

    if __name__ == '__main__':
        setLoggerConfig(args.log, args.verbose)

    NAME_POLICY = 'soft' if args.soft else 'hard'

    with openFile(args.intents, 'r') as intentsFile:
        intentsJSON = json.load(intentsFile)

    # process all intents
    for intentJSON in intentsJSON:
        examples = []
        # process all example sentences
        for exampleJSON in intentJSON["examples"]:
            examples.append(exampleJSON["text"].strip().lower())
        # new intent file
        intentFileName = os.path.join(args.intentsDir, toIntentName(NAME_POLICY, args.common_intents_nameCheck, intentJSON["intent"]) + ".csv")
        with openFile(intentFileName, "w") as intentFile:
            for example in examples:
                intentFile.write((example + "\n"))

    logger.verbose("Intents from file '%s' were successfully extracted\n", args.intents)

if __name__ == '__main__':
    main(sys.argv[1:])
