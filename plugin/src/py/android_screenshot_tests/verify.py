import os
import xml.etree.ElementTree as ET
from PIL import Image, ImageChops
from junit_xml import TestSuite, TestCase

def _is_image_same(file1, file2):
    with Image.open(file1) as im1, Image.open(file2) as im2:
        diff_image = ImageChops.difference(im1, im2)
        try:
            return diff_image.getbbox() is None
        finally:
            diff_image.close()

def _create_test_case(screenshot):
        test_class = screenshot.find('test_class').text
        test_name = screenshot.find('test_name').text
        file_name = screenshot.find('relative_file_name').text
        return TestCase(test_name, classname=test_class, stdout=file_name, elapsed_sec=1)

def verify(record_directory, truth_directory, report_file):
    errors = []
    test_cases = []
    root = ET.parse(os.path.join(record_directory, "metadata.xml")).getroot()
    for screenshot in root.iter("screenshot"):
        test_case = _create_test_case(screenshot)
        test_cases.append(test_case)

        file_name = screenshot.find('relative_file_name').text
        actual = os.path.join(record_directory, file_name)
        expected = os.path.join(truth_directory, file_name)

        same_image = _is_image_same(expected, actual)
        if not same_image:
            errors.append("Image %s is not same as %s" % (actual, expected))
            test_case.add_failure_info(message="Image does not match")

    test_suite = TestSuite("Screenshot Tests", test_cases)
    with open(report_file, 'w') as file:
        TestSuite.to_file(file, [test_suite])

    return errors