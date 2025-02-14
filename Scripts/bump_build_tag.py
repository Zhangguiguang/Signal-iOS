#!/usr/bin/env python
import sys
import os
import re
import commands
import subprocess
import argparse
import inspect
from datetime import date

def fail(message):
    file_name = __file__
    current_line_no = inspect.stack()[1][2]
    current_function_name = inspect.stack()[1][3]
    print 'Failure in:', file_name, current_line_no, current_function_name
    print message
    sys.exit(1)


def execute_command(command):
    try:
        print ' '.join(command)
        output = subprocess.check_output(command)
        if output:
            print output
    except subprocess.CalledProcessError as e:
        print e.output
        sys.exit(1)


def find_project_root():
    path = os.path.abspath(os.curdir)

    while True:
        # print 'path', path
        if not os.path.exists(path):
            break
        git_path = os.path.join(path, '.git')
        if os.path.exists(git_path):
            return path
        new_path = os.path.abspath(os.path.dirname(path))
        if not new_path or new_path == path:
            break
        path = new_path

    fail('Could not find project root path')


def is_valid_version_1(value):
    regex = re.compile(r'^(\d+)$')
    match = regex.search(value)
    return match is not None


def is_valid_version_3(value):
    regex = re.compile(r'^(\d+)\.(\d+)\.(\d+)$')
    match = regex.search(value)
    return match is not None


def is_valid_version_4(value):
    regex = re.compile(r'^(\d+)\.(\d+)\.(\d+).(\d+)$')
    match = regex.search(value)
    return match is not None


def set_versions(plist_file_path, release_version, build_version_1, build_version_4):
    if not is_valid_version_3(release_version):
        fail('Invalid release version: %s' % release_version)
    if not is_valid_version_1(build_version_1):
        fail('Invalid build version 1: %s' % build_version_1)
    if not is_valid_version_4(build_version_4):
        fail('Invalid build version 4: %s' % build_version_4)

    with open(plist_file_path, 'rt') as f:
        text = f.read()
    # print 'text', text

    # CFBundleShortVersionString is the release version.
    #
    # <key>CFBundleShortVersionString</key>
    # <string>2.20.0</string>
    file_regex = re.compile(r'<key>CFBundleShortVersionString</key>\s*<string>([\d\.]+)</string>', re.MULTILINE)
    file_match = file_regex.search(text)
    # print 'match', match
    if not file_match:
        fail('Could not parse .plist')
    text = text[:file_match.start(1)] + release_version + text[file_match.end(1):]

    # CFBundleVersion is the build version 1.
    #
    # <key>CFBundleVersion</key>
    # <string>3</string>
    file_regex = re.compile(r'<key>CFBundleVersion</key>\s*<string>([\d\.]+)</string>', re.MULTILINE)
    file_match = file_regex.search(text)
    # print 'match', match
    if not file_match:
        fail('Could not parse .plist')
    text = text[:file_match.start(1)] + build_version_1 + text[file_match.end(1):]

    # The build version 4.
    #
    # <key>OWSBundleVersion4</key>
    # <string>2.20.0.3</string>
    file_regex = re.compile(r'<key>OWSBundleVersion4</key>\s*<string>([\d\.]+)</string>', re.MULTILINE)
    file_match = file_regex.search(text)
    # print 'match', match
    if not file_match:
        fail('Could not parse .plist')
    text = text[:file_match.start(1)] + build_version_4 + text[file_match.end(1):]

    with open(plist_file_path, 'wt') as f:
        f.write(text)


# Represents a version string with 1 values, e.g. 1.
class Version1:
    def __init__(self, build):
        self.build = build
        
    def formatted(self):
        return str(self.build)



# Represents a version string with 3 dotted values, e.g. 1.2.3.
class Version3:
    def __init__(self, major, minor, patch):
        self.major = major
        self.minor = minor
        self.patch = patch
        
    def formatted(self):
        return str(self.major) + "." + str(self.minor) + "." + str(self.patch)


# Represents a version string with 4 dotted values, e.g. 1.2.3.4.
class Version4:
    def __init__(self, major, minor, patch, build):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.build = build
        
    def formatted(self):
        return str(self.major) + "." + str(self.minor) + "." + str(self.patch) + "." + str(self.build)


def parse_version_3(text):
   # print 'text', text
   regex = re.compile(r'^(\d+)\.(\d+)\.(\d+)$')
   match = regex.search(text)
   # print 'match', match
   if not match:
       fail('Could not parse .plist')
   if len(match.groups()) != 3:
       fail('Could not parse .plist')
   major = int(match.group(1))
   minor = int(match.group(2))
   patch = int(match.group(3))

   version = Version3(major, minor, patch)
   
   # Verify that roundtripping yields the same value.
   if version.formatted() != text:
       fail('Could not parse .plist')
   
   return version


def parse_version_1(text):
   build = int(text)

   version = Version1(build)
   
   # Verify that roundtripping yields the same value.
   if version.formatted() != text:
       fail('Could not parse .plist')
   
   return version


def get_versions(plist_file_path):
    with open(plist_file_path, 'rt') as f:
        text = f.read()
    # print 'text', text

    # CFBundleShortVersionString identifies the release track.
    # CFBundleVersion uniqely identifies the build within the release track.
    #  
    # Previously, we used version strings like this:
    #
    # <key>CFBundleShortVersionString</key>
    # <string>2.13.0</string>
    # <key>CFBundleVersion</key>
    # <string>2.13.0.13</string>
    #
    # We now use version strings like this:
    #
    # <key>CFBundleShortVersionString</key>
    # <string>2.13.0</string>
    # <key>CFBundleVersion</key>
    # <string>13</string>
    # <key>OWSBundleVersion4</key>
    # <string>2.13.0.13</string>
    #
    # See:
    #
    # * https://developer.apple.com/documentation/bundleresources/information_property_list/cfbundleshortversionstring
    # * https://developer.apple.com/documentation/bundleresources/information_property_list/cfbundleversion
    # * https://developer.apple.com/library/archive/technotes/tn2420/_index.html
    release_version_regex = re.compile(r'<key>CFBundleShortVersionString</key>\s*<string>(\d+\.\d+\.\d+)</string>', re.MULTILINE)
    release_version_match = release_version_regex.search(text)
    # print 'match', match
    if not release_version_match:
        fail('Could not parse .plist')

    build_version_1_regex = re.compile(r'<key>CFBundleVersion</key>\s*<string>(\d+)</string>', re.MULTILINE)
    build_version_1_match = build_version_1_regex.search(text)
    # print 'match', match
    if not build_version_1_match:
        fail('Could not parse .plist')

    release_version_str = release_version_match.group(1)
    print 'CFBundleShortVersionString:', release_version_str
    release_version = parse_version_3(release_version_str)
    print 'old_release_version:', release_version.formatted()

    build_version_1_str = build_version_1_match.group(1)
    print 'CFBundleVersion:', build_version_1_str
    build_version_1 = parse_version_1(build_version_1_str)
    print 'old_build_version_1:', build_version_1.formatted()

    return release_version, build_version_1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Precommit cleanup script.')
    parser.add_argument('--version', help='used for starting a new version.')

    type_group = parser.add_mutually_exclusive_group()
    type_group.add_argument('--internal', action='store_true', help='used to indicate throwaway builds.')
    type_group.add_argument('--nightly', action='store_true', help='used to indicate nightly builds.')
    type_group.add_argument('--beta', action='store_true', help='used to indicate beta builds.')

    args = parser.parse_args()

    is_internal = args.internal
    is_nightly = args.nightly
    is_beta = args.beta

    project_root_path = find_project_root()
    # print 'project_root_path', project_root_path
    # plist_path
    main_plist_path = os.path.join(project_root_path, 'Signal', 'Signal-Info.plist')
    if not os.path.exists(main_plist_path):
        fail('Could not find main app info .plist')

    sae_plist_path = os.path.join(project_root_path, 'SignalShareExtension', 'Info.plist')
    if not os.path.exists(sae_plist_path):
        fail('Could not find share extension info .plist')

    nse_plist_path = os.path.join(project_root_path, 'NotificationServiceExtension', 'Info.plist')
    if not os.path.exists(nse_plist_path):
        fail('Could not find NSE info .plist')

    output = subprocess.check_output(['git', 'status', '--porcelain'])
    if len(output.strip()) > 0:
        print output
        fail('Git repository has untracked files.')
    output = subprocess.check_output(['git', 'diff', '--shortstat'])
    if len(output.strip()) > 0:
        print output
        fail('Git repository has untracked files.')

    # Ensure .plist is in xml format, not binary.
    plist_paths = [
        main_plist_path,
        sae_plist_path,
        nse_plist_path,
    ]
    for plist_path in plist_paths:
        print 'plist_path:', plist_path
            
        output = subprocess.check_output(['plutil', '-convert', 'xml1', plist_path])
        # print 'output', output

    # ---------------
    # Main App
    # ---------------

    old_release_version, old_build_version_1 = get_versions(main_plist_path)

    if args.version:
        # Bump version, reset patch to zero.
        #
        # e.g. --version 1.2.3 -> "1.2.3", "102.3.0"
        new_release_version_3 = parse_version_3(args.version.strip())
        # print 'new_release_version_3:', new_release_version_3.formatted()
        
        new_build_version_1 = Version1(0)
        new_build_version_4 = Version4(
            new_release_version_3.major,
            new_release_version_3.minor,
            new_release_version_3.patch, 
            0
        )
    else:
        # Bump patch.
        new_release_version_3 = old_release_version
        new_build_version_1 = Version1(old_build_version_1.build + 1)
        new_build_version_4 = Version4(
            new_release_version_3.major,
            new_release_version_3.minor,
            new_release_version_3.patch, 
            old_build_version_1.build + 1
        )
        
    new_release_version_3 = new_release_version_3.formatted()
    new_build_version_1 = new_build_version_1.formatted()
    new_build_version_4 = new_build_version_4.formatted()

    # For example:
    #
    # old_release_version: 5.19.0
    # old_build_version_1: 42
    # new_release_version_3: 5.19.0
    # new_build_version_1: 43
    # new_build_version_4: 5.19.0.43
    print 'new_release_version_3:', new_release_version_3
    print 'new_build_version_1:', new_build_version_1
    print 'new_build_version_4:', new_build_version_4

    for plist_path in plist_paths:
        set_versions(plist_path, new_release_version_3, new_build_version_1, new_build_version_4)
    
    # ---------------
    # Git
    # ---------------
    command = ['git', 'add', '.']
    execute_command(command)

    if is_internal:
        commit_message = '"Bump build to %s." (Internal)' % new_build_version_4
    elif is_beta:
        commit_message = '"Bump build to %s." (Beta)' % new_build_version_4
    elif is_nightly:
        commit_message = '"Bump build to %s." (nightly-%s)' % ( new_build_version_4, date.today().strftime("%m-%d-%Y") )
    else:
        commit_message = '"Bump build to %s."' % new_build_version_4
    command = ['git', 'commit', '-m', commit_message]
    execute_command(command)

    tag_name = new_build_version_4
    if is_internal:
        tag_name += "-internal"
    elif is_nightly:
        tag_name += "-nightly"
    elif is_beta:
        tag_name += "-beta"

    command = ['git', 'tag', tag_name]
    execute_command(command)


