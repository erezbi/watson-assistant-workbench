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

import json
import os
import uuid
from urllib.parse import quote

import pytest
import requests

import functions_delete_package
import functions_deploy

from ...test_utils import BaseTestCaseCapture


class TestMain(BaseTestCaseCapture):

    dataBasePath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'main_data')
    packageBase = "Package-for-WAW-CI-"

    def setup_class(cls):
        BaseTestCaseCapture.checkEnvironmentVariables(['CLOUD_FUNCTIONS_USERNAME', 'CLOUD_FUNCTIONS_PASSWORD',
                                                       'CLOUD_FUNCTIONS_NAMESPACE'])
        cls.username = os.environ['CLOUD_FUNCTIONS_USERNAME']
        cls.password = os.environ['CLOUD_FUNCTIONS_PASSWORD']
        cls.apikey = cls.username + ':' + cls.password
        cls.cloudFunctionsUrl = os.environ.get('CLOUD_FUNCTIONS_URL',
                                               'https://us-south.functions.cloud.ibm.com/api/v1/namespaces')
        cls.namespace = os.environ['CLOUD_FUNCTIONS_NAMESPACE']
        cls.urlNamespace = quote(cls.namespace)
        cls.actionsUrl = cls.cloudFunctionsUrl + '/' + cls.urlNamespace + '/actions/'

    def callfunc(self, *args, **kwargs):
        functions_delete_package.main(*args, **kwargs)

    def setup_method(self):
        self.package = self.packageBase + str(uuid.uuid4())

    def teardown_method(self):
        """Delete my package, if it exists."""
        existsResponse = self._getResponseFromPackage(self.package)
        if existsResponse.status_code == 200:
            params = ['-c', os.path.join(self.dataBasePath, 'exampleFunctionsEmpty.cfg'),
                '--cloudfunctions_namespace', self.namespace,
                '--cloudfunctions_url', self.cloudFunctionsUrl,
                '--cloudfunctions_package', self.package,
                '--cloudfunctions_apikey', self.apikey]
            self.t_noException([params])

    def _getResponseFromPackage(self, package):
        """Get the package with the name of self.package"""
        packageUrl = self.cloudFunctionsUrl + '/' + self.namespace + '/packages/' + package
        return requests.get(packageUrl, auth=(self.username, self.password), headers={'Content-Type': 'application/json'})

    def _checkPackageExists(self, package=None):
        """Check if the package was correctly created"""
        response = self._getResponseFromPackage(package or self.package)
        if response.status_code != 200:
            pytest.fail("The package does not exist!")

    def _checkPackageDeleted(self, package=None):
        """Check if the package was correctly deleted"""
        response = self._getResponseFromPackage(package or self.package)
        if response.status_code != 404:
            pytest.fail("The package is not deleted!")

    @pytest.mark.skipif(os.environ.get('TRAVIS_EVENT_TYPE') != "cron", reason="This test is nightly build only.")
    @pytest.mark.parametrize('useApikey', [True, False])
    def test_deleteEmptyPackage(self, useApikey):
        """Tests if functions_delete_package deletes uploaded package that is empty."""

        params = ['-c', os.path.join(self.dataBasePath, 'exampleFunctionsEmpty.cfg'),
                '--cloudfunctions_namespace', self.namespace,
                '--cloudfunctions_url', self.cloudFunctionsUrl,
                '--cloudfunctions_package', self.package]

        if useApikey:
            params.extend(['--cloudfunctions_apikey', self.apikey])
        else:
            params.extend(['--cloudfunctions_username', self.username, '--cloudfunctions_password', self.password])

        functions_deploy.main(params)
        self._checkPackageExists()
        # delete package
        self.t_noException([params])
        self._checkPackageDeleted()

    @pytest.mark.skipif(os.environ.get('TRAVIS_EVENT_TYPE') != "cron", reason="This test is nightly build only.")
    @pytest.mark.parametrize('useApikey', [True, False])
    def test_deleteNonEmptyPackageWithoutSequence(self, useApikey):
        """Tests if functions_delete_package deletes uploaded package that is not empty and doesn't have a sequence."""

        params = ['-c', os.path.join(self.dataBasePath, 'exampleFunctions.cfg'),
                '--cloudfunctions_namespace', self.namespace,
                '--cloudfunctions_url', self.cloudFunctionsUrl,
                '--cloudfunctions_package', self.package]

        if useApikey:
            params.extend(['--cloudfunctions_apikey', self.apikey])
        else:
            params.extend(['--cloudfunctions_username', self.username, '--cloudfunctions_password', self.password])

        functions_deploy.main(params)
        self._checkPackageExists()
        # delete package
        self.t_noException([params])
        self._checkPackageDeleted()

    @pytest.mark.parametrize('useApikey', [True, False])
    def test_deleteNonEmptyPackageWithSequence(self, useApikey):
        """Tests if functions_delete_package deletes uploaded package that is not empty and has a sequence."""

        params = ['-c', os.path.join(self.dataBasePath, 'exampleFunctions.cfg'),
                '--cloudfunctions_package', self.package, '--cloudfunctions_namespace', self.namespace,
                '--cloudfunctions_url', self.cloudFunctionsUrl]
        if useApikey:
            params.extend(['--cloudfunctions_apikey', self.apikey])
        else:
            params.extend(['--cloudfunctions_username', self.username, '--cloudfunctions_password', self.password])

        functions_deploy.main(params)
        self._checkPackageExists()

        sequenceUrl = self.actionsUrl + self.package + '/testSequence'
        functionsDir = os.path.join(self.dataBasePath, 'example_functions')
        functionFileNames = [os.path.basename(os.path.join(functionsDir, f)) for f in os.listdir(functionsDir)]
        # Use fully qualified names!
        functionNames = [self.namespace + '/' + self.package +'/' + os.path.splitext(fileName)[0] for fileName in functionFileNames]

        payload = {'exec': {'kind': 'sequence', 'binary': False, 'components': functionNames}}
        # Connect the functions into a sequence
        response = requests.put(sequenceUrl, auth=(self.username, self.password), headers={'Content-Type': 'application/json'},
                                    data=json.dumps(payload), verify=False)

        # Fail if sequence upload failed
        response.raise_for_status()

        # delete package
        self.t_noException([params])
        self._checkPackageDeleted()

    @pytest.mark.skipif(os.environ.get('TRAVIS_EVENT_TYPE') != "cron", reason="This test is nightly build only.")
    @pytest.mark.parametrize('useApikey', [True, False])
    def test_deleteNonexistentPackage(self, useApikey):
        """Tests if functions_delete_package errors while deleting nonexistent package."""

        randomName = str(uuid.uuid4())
        params = ['-c', os.path.join(self.dataBasePath, 'exampleFunctions.cfg'),
                '--cloudfunctions_package', randomName, '--cloudfunctions_namespace', self.namespace,
                '--cloudfunctions_url', self.cloudFunctionsUrl]

        if useApikey:
            params.extend(['--cloudfunctions_apikey', self.apikey])
        else:
            params.extend(['--cloudfunctions_username', self.username, '--cloudfunctions_password', self.password])
        # Fail
        self.t_exitCodeAndLogMessage(1, "Package not found. Check your cloudfunctions url and namespace.", [params])

    # TODO: Enable apikey/username+password testing in Nightly builds
    #@pytest.mark.parametrize('useApikey', [True, False])
    @pytest.mark.parametrize('useApikey', [True])
    def test_noPackageProvided(self, useApikey):
        """Tests if functions_delete_package errors when not providing a package or package name pattern."""

        params = ['-c', os.path.join(self.dataBasePath, 'exampleFunctions.cfg'),
                '--cloudfunctions_namespace', self.namespace,
                '--cloudfunctions_url', self.cloudFunctionsUrl]

        if useApikey:
            params.extend(['--cloudfunctions_apikey', self.apikey])
        else:
            params.extend(['--cloudfunctions_username', self.username, '--cloudfunctions_password', self.password])
        # Fail
        self.t_exitCodeAndLogMessage(1, "neither 'cloudfunctions_package' nor 'cloudfunctions_package_pattern' is defined.", [params])

    # TODO: Enable apikey/username+password testing in Nightly builds
    #@pytest.mark.parametrize('useApikey', [True, False])
    @pytest.mark.parametrize('useApikey', [True])
    def test_noMatchingPackage(self, useApikey):
        """Tests if functions_delete_package finishes successfully with no matching packages."""

        randomNamePattern = str(uuid.uuid4())
        params = ['-c', os.path.join(self.dataBasePath, 'exampleFunctions.cfg'),
                '--cloudfunctions_package_pattern', randomNamePattern, '--cloudfunctions_namespace', self.namespace,
                '--cloudfunctions_url', self.cloudFunctionsUrl]

        if useApikey:
            params.extend(['--cloudfunctions_apikey', self.apikey])
        else:
            params.extend(['--cloudfunctions_username', self.username, '--cloudfunctions_password', self.password])

        self.t_noExceptionAndLogMessage("No matching packages to delete.", [params])

    @pytest.mark.skipif(os.environ.get('TRAVIS_EVENT_TYPE') != "cron", reason="This test is nightly build only.")
    @pytest.mark.parametrize('useApikey', [True, False])
    def test_wrongCredentials(self, useApikey):
        """Tests if functions_delete_package errors while deleting with wrong credentials."""

        params = ['-c', os.path.join(self.dataBasePath, 'exampleFunctions.cfg'),
                '--cloudfunctions_package', self.package, '--cloudfunctions_namespace', self.namespace,
                '--cloudfunctions_url', self.cloudFunctionsUrl]

        # Correct params for deploy
        paramsDeploy = list(params)
        if useApikey:
            paramsDeploy.extend(['--cloudfunctions_apikey', self.apikey])
        else:
            paramsDeploy.extend(['--cloudfunctions_username', self.username, '--cloudfunctions_password', self.password])

        # Wrong params for delete
        paramsDelete = list(params)
        randomUsername = str(uuid.uuid4())
        randomPassword = str(uuid.uuid4())
        if useApikey:
            paramsDelete.extend(['--cloudfunctions_apikey', randomUsername + ':' + randomPassword])
        else:
            paramsDelete.extend(['--cloudfunctions_username', randomUsername, '--cloudfunctions_password', randomPassword])

        # Pass
        functions_deploy.main(paramsDeploy)
        self._checkPackageExists()

        # Fail
        self.t_exitCodeAndLogMessage(1, "Authorization error. Check your credentials.", [paramsDelete])

    @pytest.mark.skipif(os.environ.get('TRAVIS_EVENT_TYPE') != "cron", reason="This test is nightly build only.")
    @pytest.mark.parametrize('useApikey', [True, False])
    def test_wrongCloudfunctionsUrl(self, useApikey):
        """Tests if functions_delete_package errors while deleting with wrong cloud functions url."""

        params = ['-c', os.path.join(self.dataBasePath, 'exampleFunctions.cfg'),
                '--cloudfunctions_package', self.package, '--cloudfunctions_namespace', self.namespace]
        if useApikey:
            params.extend(['--cloudfunctions_apikey', self.apikey])
        else:
            params.extend(['--cloudfunctions_username', self.username, '--cloudfunctions_password', self.password])

        # Correct params for deploy
        paramsDeploy = list(params)
        paramsDeploy.extend(['--cloudfunctions_url', self.cloudFunctionsUrl])
        # Wrong params for delete
        paramsDelete = list(params)
        paramsDelete.extend(['--cloudfunctions_url', self.cloudFunctionsUrl+str(uuid.uuid4())])

        # Pass
        functions_deploy.main(paramsDeploy)
        self._checkPackageExists()

        # Fail
        self.t_exitCodeAndLogMessage(1,
        "The resource could not be found. Check your cloudfunctions url and namespace.", [paramsDelete])

    @pytest.mark.skipif(os.environ.get('TRAVIS_EVENT_TYPE') != "cron", reason="This test is nightly build only.")
    @pytest.mark.parametrize('useApikey', [True, False])
    def test_wrongNamespace(self, useApikey):
        """Tests if functions_delete_package errors while deleting with wrong namespace."""

        params = ['-c', os.path.join(self.dataBasePath, 'exampleFunctions.cfg'),
                '--cloudfunctions_package', self.package, '--cloudfunctions_url', self.cloudFunctionsUrl]
        if useApikey:
            params.extend(['--cloudfunctions_apikey', self.apikey])
        else:
            params.extend(['--cloudfunctions_username', self.username, '--cloudfunctions_password', self.password])

        # Correct params for deploy
        paramsDeploy = list(params)
        paramsDeploy.extend(['--cloudfunctions_namespace', self.namespace])
        # Wrong params for delete
        paramsDelete = list(params)
        paramsDelete.extend(['--cloudfunctions_namespace', self.namespace + self.cloudFunctionsUrl+str(uuid.uuid4())])

        # Pass
        functions_deploy.main(paramsDeploy)
        self._checkPackageExists()

        # Fail
        self.t_exitCodeAndLogMessage(1,
        "The resource could not be found. Check your cloudfunctions url and namespace.", [paramsDelete])

    @pytest.mark.parametrize('useApikey', [True])
    def test_deletePackageByRegex(self, useApikey):
        """Tests if functions_delete_package deletes uploaded packages by regex matching."""

        params = ['-c', os.path.join(self.dataBasePath, 'exampleFunctionsEmpty.cfg'),
                '--cloudfunctions_namespace', self.namespace,
                '--cloudfunctions_url', self.cloudFunctionsUrl]

        if useApikey:
            params.extend(['--cloudfunctions_apikey', self.apikey])
        else:
            params.extend(['--cloudfunctions_username', self.username, '--cloudfunctions_password', self.password])

        createdPackages = []
        nonmatchingPackageName = None
        # Generate random packages with common prefix and delete them afterwards
        for i in range(4):
            newParams = list(params)
            # Add one package that doesn't match (will check if it wasn't deleted)
            if i == 0:
                newPackage = self.packageBase + "NONMATCHINGREGEX-" + str(uuid.uuid4())
                nonmatchingPackageName = newPackage
            else:
                newPackage = self.packageBase + "REGEX-" + str(uuid.uuid4())
            newParams.extend(['--cloudfunctions_package', newPackage])
            functions_deploy.main(newParams)
            self._checkPackageExists(newPackage)
            createdPackages.append(newPackage)

        # delete the packages
        newParams = list(params)
        newParams.extend(['--cloudfunctions_package_pattern', '^' + self.packageBase + 'REGEX-.*'])
        self.t_noException([newParams])

        # Check that the correct packages were deleted
        for package in createdPackages:
            if package != nonmatchingPackageName:
                self._checkPackageDeleted(package)

        # Check that the nonmatching package still exists
        self._checkPackageExists(nonmatchingPackageName)

        # Delete the nonmatching package
        newParams = list(params)
        newParams.extend(['--cloudfunctions_package_pattern', '^' + self.packageBase + 'NONMATCHINGREGEX-.*'])
        self.t_noException([newParams])
        self._checkPackageDeleted(nonmatchingPackageName)

    def test_badArgs(self):
        """Tests some basic common problems with args."""
        self.t_unrecognizedArgs([['--nonExistentArg', 'randomNonPositionalArg']])
        self.t_exitCode(1, [[]])

        completeArgsList = ['--cloudfunctions_username', self.username,
                            '--cloudfunctions_password', self.password,
                            '--cloudfunctions_apikey', self.username + ":" + self.password,
                            '--cloudfunctions_package', self.package,
                            '--cloudfunctions_namespace', self.namespace,
                            '--cloudfunctions_url', self.cloudFunctionsUrl]

        for argIndex in range(len(completeArgsList)):
            if not completeArgsList[argIndex].startswith('--'):
                continue
            paramName = completeArgsList[argIndex][2:]

            argsListWithoutOne = []
            for i in range(len(completeArgsList)):
                if i != argIndex and i != (argIndex + 1):
                    argsListWithoutOne.append(completeArgsList[i])

            if paramName in ['cloudfunctions_username', 'cloudfunctions_password']:
                message = 'combination already set: \'[\'cloudfunctions_apikey\']\''
            elif paramName in ['cloudfunctions_apikey']:
                # we have to remove username and password (if not it would be valid combination of parameters)
                argsListWithoutOne = argsListWithoutOne[4:] # remove username and password (leave just apikey)
                message = 'Combination 0: \'cloudfunctions_apikey\''
            else:
                # we have to remove username and password (if not then it would always return error that both auth types are provided)
                argsListWithoutOne = argsListWithoutOne[4:] # remove username and password (leave just apikey)
                message = 'required \'' + paramName + '\' parameter not defined'
            if paramName == "cloudfunctions_package":
                self.t_exitCodeAndLogMessage(1, "neither 'cloudfunctions_package' nor 'cloudfunctions_package_pattern' is defined.", [argsListWithoutOne])
            else:
                self.t_exitCodeAndLogMessage(1, message, [argsListWithoutOne])
