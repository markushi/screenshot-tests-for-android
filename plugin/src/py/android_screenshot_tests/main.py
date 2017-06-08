import sys
import getopt
import os
import common
import shutil
import zipfile

import pull_screenshots
import verify
import aapt
from .simple_puller import SimplePuller

def usage():
    print("usage: ./main.py --verify --verify-dir <package-name> [--no-pull --record-dir --apk]")
    print("usage: ./main.py --record --verify-dir <package-name> [--no-pull]")
    return

def copy_web(destination):
    source = os.path.dirname(__file__)
    while not os.path.isfile(source):
        source = os.path.dirname(source)

    with zipfile.ZipFile(source) as archive:
        for file in archive.namelist():
            if file.endswith('/'):
                continue
            if file.startswith('android_screenshot_tests/web/'):
                path = file[len('android_screenshot_tests/web/'):]
                folder_name = os.path.join(destination, path[:path.rindex('/')]) if '/' in path else destination
                file_name = path[path.rindex('/')+1:] if '/' in path else path
                file_name_full = os.path.join(folder_name, file_name)

                if not os.path.exists(folder_name):
                    os.makedirs(folder_name)
                with open(file_name_full, 'wb') as f:
                    f.write(archive.read(file))

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

        copy_web(record_directory)
        report_file = os.path.join(record_directory, 'screenshot_report.xml')
        errors = verify.verify(
            record_directory, reference_directory, report_file)
        if len(errors) > 0:
            print("\n".join(errors))
            return 1

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
