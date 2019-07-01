"""
Copyright 2019 IBM Corporation
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

import os

from lxml import etree

import dialog_json2xml

from ...test_utils import BaseTestCaseCapture


class TestMain(BaseTestCaseCapture):

    dataBasePath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'main_data')
    testOutputPath = os.path.join(dataBasePath, 'outputs')


    def setup_class(cls):
        ''' Setup any state specific to the execution of the given class (which usually contains tests). '''
        # create output folder
        BaseTestCaseCapture.createFolder(TestMain.testOutputPath)

    def callfunc(self, *args, **kwargs):
        dialog_json2xml.main(*args, **kwargs)

    def _assertXmlEqual(self, xml1path, xml2path):
        """Tests if two xml files are equal."""
        with open(xml1path, 'r') as xml1File:
            xml1 = etree.XML(xml1File.read(), etree.XMLParser(remove_blank_text=True))
            for parent in xml1.xpath('//*[./*]'): # Search for parent elements
                parent[:] = sorted(parent, key=lambda x: x.tag)
        with open(xml2path, 'r') as xml2File:
            xml2 = etree.XML(xml2File.read(), etree.XMLParser(remove_blank_text=True))
            for parent in xml2.xpath('//*[./*]'): # Search for parent elements
                parent[:] = sorted(parent, key=lambda x: x.tag)

        assert etree.tostring(xml1) == etree.tostring(xml2)

    def test_mainValidActions(self):
        """Tests if the script successfully completes with valid input file with actions."""
        inputJsonPath = os.path.abspath(os.path.join(self.dataBasePath, 'inputActionsValid.json'))
        expectedXmlPath = os.path.abspath(os.path.join(self.dataBasePath, 'expectedActionsValid.xml'))

        outputXmlDirPath = os.path.join(self.testOutputPath, 'outputActionsValidResult')
        outputXmlPath = os.path.join(outputXmlDirPath, 'dialog.xml')

        BaseTestCaseCapture.createFolder(outputXmlDirPath)

        self.t_noException([[inputJsonPath, '-d', outputXmlDirPath]])
        self._assertXmlEqual(expectedXmlPath, outputXmlPath)

    def test_mainValidNodeTypes(self):
        """Tests if the script successfully completes with valid input file with node types."""
        inputJsonPath = os.path.abspath(os.path.join(self.dataBasePath, 'inputNodeTypesValid.json'))
        expectedXmlPath = os.path.abspath(os.path.join(self.dataBasePath, 'expectedNodeTypesValid.xml'))

        outputXmlDirPath = os.path.join(self.testOutputPath, 'outputNodeTypesValidResult')
        outputXmlPath = os.path.join(outputXmlDirPath, 'dialog.xml')

        BaseTestCaseCapture.createFolder(outputXmlDirPath)

        self.t_noException([[inputJsonPath, '-d', outputXmlDirPath]])
        self._assertXmlEqual(expectedXmlPath, outputXmlPath)


    def test_mainValidBool(self):
        """Tests if the script successfully completes with valid input file with bool."""
        inputJsonPath = os.path.abspath(os.path.join(self.dataBasePath, 'inputBoolValid.json'))
        expectedXmlPath = os.path.abspath(os.path.join(self.dataBasePath, 'expectedBoolValid.xml'))

        outputXmlDirPath = os.path.join(self.testOutputPath, 'outputBoolValidResult')
        outputXmlPath = os.path.join(outputXmlDirPath, 'dialog.xml')

        BaseTestCaseCapture.createFolder(outputXmlDirPath)

        self.t_noException([[inputJsonPath, '-d', outputXmlDirPath]])
        self._assertXmlEqual(expectedXmlPath, outputXmlPath)
