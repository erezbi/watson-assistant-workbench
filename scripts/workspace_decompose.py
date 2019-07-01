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
import sys

from wawCommons import getScriptLogger, openFile, setLoggerConfig

logger = getScriptLogger(__file__)

def main(argv):
    parser = argparse.ArgumentParser(description='Decompose Bluemix conversation service workspace in .json format to intents json, entities json and dialog json', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # positional arguments
    parser.add_argument('workspace', help='workspace in .json format')
    # optional arguments
    parser.add_argument('-i','--intents', required=False, help='file with intents in .json format (not extracted if not specified)')
    parser.add_argument('-e','--entities', required=False, help='file with entities in .json format (not extracted if not specified)')
    parser.add_argument('-d','--dialog', required=False, help='file with dialog in .json format (not extracted if not specified)')
    parser.add_argument('-c','--counterexamples', required=False, help='file with counterexamples in .json format (not extracted if not specified)')
    parser.add_argument('-v','--verbose', required=False, help='verbosity', action='store_true')
    parser.add_argument('--log', type=str.upper, default=None, choices=list(logging._levelToName.values()))
    args = parser.parse_args(argv)

    if __name__ == '__main__':
        setLoggerConfig(args.log, args.verbose)

    with openFile(args.workspace, 'r') as workspaceFile:
        workspaceJSON = json.load(workspaceFile)

    if args.intents:
        with openFile(args.intents, 'w') as intentsFile:
            intentsFile.write(json.dumps(workspaceJSON['intents'], indent=4, ensure_ascii=False))

    if args.entities:
        with openFile(args.entities, 'w') as entitiesFile:
            entitiesFile.write(json.dumps(workspaceJSON['entities'], indent=4, ensure_ascii=False))

    if args.dialog:
        with openFile(args.dialog, 'w') as dialogFile:
            dialogFile.write(json.dumps(workspaceJSON['dialog_nodes'], indent=4, ensure_ascii=False))

    if args.counterexamples:
        with openFile(args.counterexamples, 'w') as counterexamplesFile:
            counterexamplesJSON = []
            counterexampleIntentJSON = {}
            counterexampleIntentJSON['intent'] = "IRRELEVANT"
            counterexampleIntentJSON['examples'] = workspaceJSON['counterexamples']
            counterexamplesJSON.append(counterexampleIntentJSON)
            counterexamplesFile.write(json.dumps(counterexamplesJSON, indent=4, ensure_ascii=False))

    logger.verbose("Workspace %s was successfully decomposed", args.workspace)

if __name__ == '__main__':
    main(sys.argv[1:])
