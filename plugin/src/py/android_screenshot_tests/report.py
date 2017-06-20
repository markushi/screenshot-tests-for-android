#!/usr/bin/env python
#
# Copyright (c) 2014-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#

import os
import sys
import subprocess
import shutil
import zipfile

from mako.template import Template
from mako import exceptions
from junit_xml import TestSuite, TestCase


def _copy_web_assets(destination):
    # web assets can either be in a local directory or bundled inside the plugin zip file
    if os.path.isfile(__file__):
        source = os.path.join(os.path.dirname(__file__), 'web')
        shutil.copytree(source, destination)
        return

    # find the zip file
    source = __file__
    while not os.path.isfile(source):
        source = os.path.dirname(source)

    with zipfile.ZipFile(source) as archive:
        for file in archive.namelist():
            # don't copy directory zip entries
            if file.endswith('/'):
                continue
            if file.startswith('android_screenshot_tests/web/'):
                path = file[len('android_screenshot_tests/web/'):]
                folder_name = os.path.join(destination, path[:path.rindex('/')]) if '/' in path else destination
                
                file_name = path[path.rindex('/') + 1:] if '/' in path else path
                file_name_full = os.path.join(folder_name, file_name)

                if not os.path.exists(folder_name):
                    os.makedirs(folder_name)
                with open(file_name_full, 'wb') as f:
                    f.write(archive.read(file))


def generate_web_report(test_report, output_directory):
    _copy_web_assets(output_directory)

    html_template = os.path.join(output_directory, 'template.html')
    html_file = os.path.join(output_directory, 'index.html')
    template = Template(filename=html_template)

    with open(html_file, 'w') as file:
        try:
            file.write(template.render(data=test_report))
        except:
            file.write(exceptions.html_error_template().render())


if __name__ == '__main__':
    test_cases = []
    test_case = TestCase('hallo', classname='welt',
                         stdout='file_name', elapsed_sec=1)
    test_case.add_failure_info(message="Image does not match")
    test_cases.append(test_case)

    test_case = TestCase('fixit', classname='Max',
                         stdout='file_2', elapsed_sec=1)
    test_cases.append(test_case)

    test_report = TestSuite("Screenshot Tests", test_cases)

    tmp = '/tmp/test'
    if os.path.exists(tmp):
        shutil.rmtree(tmp)

    generate_web_report(test_report, tmp)
