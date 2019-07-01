'''
Copyright 2018 IBM Corporation
Licensed under the Apache License, Version 2.0 (the 'License');
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an 'AS IS' BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import argparse
import json
import logging
import os
import sys

from cfgCommons import Cfg
from wawCommons import (convertApikeyToUsernameAndPassword,
                        getFunctionResponseJson, getOptionalParameter,
                        getParametersCombination, getRequiredParameter,
                        getScriptLogger, getTimestampInMillis,
                        replaceValue, setLoggerConfig)
from ExceptionCommons import CFCallException

logger = getScriptLogger(__file__)

def main(argv):
    parser = argparse.ArgumentParser(description='Tests all tests specified in given file against Cloud Functions and save test outputs to output file', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # positional arguments
    parser.add_argument('inputFileName', help='File with json array containing tests.')
    parser.add_argument('outputFileName', help='File where to store test outputs.')
    # optional arguments
    parser.add_argument('-c', '--common_configFilePaths', help='configuaration file', action='append')
    parser.add_argument('--cloudfunctions_url', required=False, help='url of cloud functions API')
    parser.add_argument('--cloudfunctions_namespace', required=False, help='cloud functions namespace')
    parser.add_argument('--cloudfunctions_package', required=False, help='cloud functions package name')
    parser.add_argument('--cloudfunctions_function', required=False, help='cloud functions specific function to be tested')
    parser.add_argument('--cloudfunctions_apikey', required=False, help="cloud functions apikey")
    parser.add_argument('--cloudfunctions_username', required=False, help='cloud functions user name')
    parser.add_argument('--cloudfunctions_password', required=False, help='cloud functions password')
    parser.add_argument('-v','--verbose', required=False, help='verbosity', action='store_true')
    parser.add_argument('--log', type=str.upper, default=None, choices=list(logging._levelToName.values()))
    parser.add_argument('--replace', required=False, help='string values to be replaced in input and expected output json (format \'valueToBeReplaced1:replacement1,valueToBeReplaced2:replacement2\')')
    parser.add_argument('-t','--time', required=False, help='measure time of each test', action='store_true')
    args = parser.parse_args(argv)

    if __name__ == '__main__':
        setLoggerConfig(args.log, args.verbose)

    config = Cfg(args)

    logger.info('STARTING: '+ os.path.basename(__file__))

    url = getRequiredParameter(config, 'cloudfunctions_url')
    namespace = getRequiredParameter(config, 'cloudfunctions_namespace')
    auth = getParametersCombination(config, 'cloudfunctions_apikey', ['cloudfunctions_password', 'cloudfunctions_username'])
    package = getOptionalParameter(config, 'cloudfunctions_package')
    function = getOptionalParameter(config, 'cloudfunctions_function')

    time = getOptionalParameter(config, 'time')

    if 'cloudfunctions_apikey' in auth:
        username, password = convertApikeyToUsernameAndPassword(auth['cloudfunctions_apikey'])
    else:
        username = auth['cloudfunctions_username']
        password = auth['cloudfunctions_password']

    try:
        inputFile = open(args.inputFileName, 'r')
    except IOError:
        logger.critical("Cannot open test input file '%s'", args.inputFileName)
        sys.exit(1)

    try:
        outputFile = open(args.outputFileName, 'w')
    except IOError:
        logger.critical("Cannot open test output file '%s'", args.outputFileName)
        sys.exit(1)

    try:
        inputJson = json.load(inputFile)
    except ValueError as e:
        logger.critical("Cannot decode json from test input file '%s', error '%s'", args.inputFileName, str(e))
        sys.exit(1)

    if not isinstance(inputJson, list):
        logger.critical("Input test json is not array!")
        sys.exit(1)

    replaceDict = {}
    for attr in dir(config):
        if not attr.startswith("__"):
            if attr == 'replace':
                # format \'valueToBeReplaced1:replacement1,valueToBeReplaced2:replacement2\'
                replacementsString = getattr(config, attr)
                for replacementString in replacementsString.split(','):
                    replacementStringSplit = replacementString.split(':')
                    if len(replacementStringSplit) != 2 or not replacementStringSplit[0] or not replacementStringSplit[1]:
                        logger.critical("Invalid format of 'replace' parameter, valid format is 'valueToBeReplaced1:replacement1,valueToBeReplaced2:replacement2'")
                        sys.exit(1)
                    replaceDict[replacementStringSplit[0]] = replacementStringSplit[1]
            else:
                replaceDict[attr] = getattr(config, attr)

    # helper to create error errorMessage
    def errorJsonTemplate(message, type):
        return { 'message': message, 'type': type }

    # helper to set 'end' and 'time' in test jsons
    def setDuration(test):
        if time:
            test['end'] = getTimestampInMillis()
            test['time'] = test['end'] - test['start']
        return test

    # run tests
    testCounter = -1
    for test in inputJson:
        if time:
            test['start'] = getTimestampInMillis()
        testCounter += 1
        if not isinstance(test, dict):
            errorMessage = "Input test array element {:d} is not dictionary. Each test has to be dictionary, please see doc!".format(testCounter)
            logger.error(errorMessage)
            inputJson[testCounter] = {}
            inputJson[testCounter]['error'] = errorJsonTemplate(errorMessage, 'ValueError')
            test = setDuration(test)
            continue
        logger.info("Test number %d, name '%s'", testCounter, (test['name'] if 'name' in test else '-'))

        # load test input payload json
        testInputJson = test['input']
        testInputPath = None
        try:
            if testInputJson.startswith('@'):
                testInputPath = os.path.join(os.path.dirname(args.inputFileName), testInputJson[1:])
                logger.debug('Loading input payload from file: %s', testInputPath)
                try:
                    inputFile = open(testInputPath, 'r')
                except IOError:
                    errorMessage = "Cannot open input payload from file '{}'".format(testInputPath)
                    logger.error(errorMessage)
                    test['error'] = errorJsonTemplate(errorMessage, 'IOError')
                    test = setDuration(test)
                    continue
                try:
                    testInputJson = json.load(inputFile)
                except ValueError as e:
                    errorMessage = "Cannot decode json from input payload from file '{}', error '{}'".format(testInputPath, str(e))
                    logger.error(errorMessage)
                    test['error'] = errorJsonTemplate(errorMessage, 'IOError')
                    test = setDuration(test)
                    continue
        except AttributeError:
            pass

        if not testInputPath:
            logger.debug('Input payload provided inside the test')

        # load test expected output payload json
        testOutputExpectedJson = test['outputExpected']
        testOutputExpectedPath = None
        try:
            if testOutputExpectedJson.startswith('@'):
                testOutputExpectedPath = os.path.join(os.path.dirname(args.inputFileName), testOutputExpectedJson[1:])
                logger.debug('Loading expected output payload from file: %s', testOutputExpectedPath)
                try:
                    outputExpectedFile = open(testOutputExpectedPath, 'r')
                except IOError:
                    errorMessage = "Cannot open expected output payload from file '{}'".format(testOutputExpectedPath)
                    logger.error(errorMessage)
                    test['error'] = errorJsonTemplate(errorMessage, 'IOError')
                    test = setDuration(test)
                    continue
                try:
                    testOutputExpectedJson = json.load(outputExpectedFile)
                except ValueError as e:
                    errorMessage = "Cannot decode json from expected output payload from file '{}', error '{}'".format(testOutputExpectedPath, str(e))
                    logger.error(errorMessage)
                    test['error'] = errorJsonTemplate(errorMessage, 'IOError')
                    test = setDuration(test)
                    continue
        except AttributeError:
            pass

        if not testOutputExpectedPath:
            logger.debug('Expected output payload provided inside the test')

        logger.debug('Replacing values in input and expected output jsons by configuration parameters.')

        for target, value in replaceDict.items():
            testInputJson, replacementNumber = replaceValue(testInputJson, '::' + target, value, False)
            if replacementNumber > 0:
                logger.debug('Replaced configuration parameter \'%s\' in input json, number of occurences: %d.', target, replacementNumber)
            testOutputExpectedJson, replacementNumber = replaceValue(testOutputExpectedJson, '::' + target, value, False)
            if replacementNumber > 0:
                logger.debug('Replaced configuration parameter \'%s\' in expected output json, number of occurences: %d.', target, replacementNumber)

        # save the expected output as an object even it was specified as a file,
        # because it can contain replaced value and the returned output is also an object
        # (could be improved by parameter that save both to external files)
        test['outputExpected'] = testOutputExpectedJson

        # call CF
        try:
            logger.debug('Sending input json: %s', json.dumps(testInputJson, ensure_ascii=False).encode('utf8'))
            testOutputReturnedJson = getFunctionResponseJson(
                url,
                namespace,
                username,
                password,
                (test['cf_package'] if 'cf_package' in test else package),
                (test['cf_function'] if 'cf_function' in test else function),
                {},
                testInputJson)

            logger.debug('Received output json: %s', json.dumps(testOutputReturnedJson, ensure_ascii=False).encode('utf8'))
            test['outputReturned'] = testOutputReturnedJson
        except CFCallException as e:
            test['error'] = e.toJson()
        test = setDuration(test)

    outputFile.write(json.dumps(inputJson, indent=4, ensure_ascii=False) + '\n')
    outputFile.close()
    logger.info('FINISHING: '+ os.path.basename(__file__))

if __name__ == '__main__':
    main(sys.argv[1:])
