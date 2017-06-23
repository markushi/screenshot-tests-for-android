import sys
import getopt
import os
import common
import shutil
from junit_xml import TestSuite

from . import aapt
from . import pull_screenshots
from .simple_puller import SimplePuller
from .report import generate_web_report
from . import verify

def usage():
    print("usage: ./main.py --verify --verify-dir=<dir> <package-name> [--no-pull --record-dir=<dir> --apk]")
    print("usage: ./main.py --record --verify-dir=<dir> <package-name> [--no-pull]")
    return

def copytree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                shutil.copy2(s, d)


def build_puller_args(opts):
    puller_args = []
    if "-e" in opts:
        puller_args.append("-e")

    if "-d" in opts:
        puller_args.append("-d")

    if "-s" in opts:
        puller_args += ["-s", opts["-s"]]
    return puller_args


def main(argv):
    common.setup_paths()
    try:
        opt_list, rest_args = getopt.gnu_getopt(
            argv[1:],
            "eds:",
            ["generate-png=", "filter-name-regex=", "apk", "record", "verify", "verify-dir=", "record-dir=", "no-pull", "report-dir="])
    except getopt.GetoptError as err:
        usage()
        return 2

    if len(rest_args) != 1:
        # missing package/apk name
        usage()
        return 2

    opts = dict(opt_list)
    record_mode = '--record' in opts
    verify_directory = opts.get('--verify-dir')
    record_directory = opts.get('--record-dir')

    package = ''
    if "--apk" in opts:
        package = aapt.get_package(rest_args[0])
    else:
        package = rest_args[0]

    if "--no-pull" not in opts:
        if os.path.exists(record_directory):
            shutil.rmtree(record_directory)

        puller_args = build_puller_args(opts)
        pull_screenshots.pull(package,
                                destination_dir=record_directory,
                                adb_puller=SimplePuller(puller_args),
                                filter_name_regex=opts.get('--filter-name-regex'))

    if record_mode:
        if os.path.exists(verify_directory):
            shutil.rmtree(verify_directory)
        shutil.copytree(record_directory, verify_directory)
    else:
        # verify mode
        reference_directory = os.path.join(record_directory, 'expected')
        if os.path.exists(reference_directory):
            shutil.rmtree(reference_directory)
        copytree(verify_directory, reference_directory)

        test_report, errors = verify.verify(record_directory, reference_directory)

        test_report_file = os.path.join(record_directory, 'screenshot_report.xml')
        with open(test_report_file, 'w') as file:
            TestSuite.to_file(file, [test_report])

        generate_web_report(test_report, record_directory)

        print("\nTo review the screenshot test results navigate to:\n\tfile://%s/index.html\n\n" % record_directory)

        if len(errors) > 0:
            print("\n".join(errors))
            return 1

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
