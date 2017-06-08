#!/usr/bin/env python
#
# Copyright (c) 2014-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import os
import sys
import tempfile
import subprocess
import xml.etree.ElementTree as ET
import getopt
import shutil
import zipfile

from os.path import join
from os.path import abspath

from junit_xml import TestSuite, TestCase

from .aapt import *
from .common import *
from .simple_puller import *
from .metadata import *

def _android_path_join(*args):
    """Similar to os.path.join(), but might differ in behavior on Windows"""
    path = args[0]
    for part in args[1:]:
        if path.endswith('/') and part.startswith('/'):
            path = path + part[1:]
        elif path.endswith('/') or part.startswith('/'):
            path = path + part
        else:
            path = path + '/' + part
    return path

def _pull_metadata(package, dir, adb_puller):
    metadata_file = _android_path_join(adb_puller.get_external_data_dir(), 
        "screenshots",
        package,
        'screenshots-default',
        'metadata.xml')

    if adb_puller.remote_file_exists(metadata_file):
        adb_puller.pull(metadata_file, join(dir, 'metadata.xml'))
    else:
        _create_empty_metadata_file(dir)

    return metadata_file.replace("metadata.xml", "")

def _create_empty_metadata_file(dir):
    with open(join(dir, 'metadata.xml'), 'w') as out:
        out.write(

    """<?xml version="1.0" encoding="UTF-8"?>
<screenshots>
</screenshots>""")

def _pull_images(dir, device_dir, adb_puller):
    root = ET.parse(join(dir, 'metadata.xml')).getroot()
    for s in root.iter('screenshot'):
        filename_nodes = s.findall('relative_file_name')
        for filename_node in filename_nodes:
            adb_puller.pull(
                _android_path_join(device_dir, filename_node.text),
                join(dir, os.path.basename(filename_node.text)))
        dump_node = s.find('view_hierarchy')
        if dump_node is not None:
            adb_puller.pull(_android_path_join(device_dir, dump_node.text), join(dir, os.path.basename(dump_node.text)))

def _pull_filtered(package, dir, adb_puller, filter_name_regex=None):
    device_dir = _pull_metadata(package, dir, adb_puller)
    _validate_metadata(dir)
    filter_screenshots(join(dir, 'metadata.xml'), name_regex=filter_name_regex)
    _pull_images(dir, device_dir, adb_puller)

def _validate_metadata(dir):
    try:
        ET.parse(join(dir, 'metadata.xml'))
    except ET.ParseError as e:
        raise RuntimeError("Unable to parse metadata file, this commonly happens if you did not call ScreenshotRunner.onDestroy() from your instrumentation")

def pull(package, adb_puller, destination_dir, filter_name_regex=None):
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    _pull_filtered(package, adb_puller=adb_puller, dir=destination_dir, filter_name_regex=filter_name_regex)
    _validate_metadata(destination_dir)

if __name__ == '__main__':
    package = sys.argv[1]
    destination_dir = sys.argv[2]
    adb_puller = SimplePuller()
    pull(package, adb_puller, destination_dir)
