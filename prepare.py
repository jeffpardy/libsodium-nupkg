#!/usr/bin/env python3

import os.path
import re
import sys

WINDOWS = [
  # --------------------- ----------------- #
  # Runtime ID            Platform          #
  # --------------------- ----------------- #
  ( 'win-x64',            'x64'             ),
  ( 'win-x86',            'Win32'           ),
  # --------------------- ----------------- #
]

MACOS = [
  # --------------------- ----------------- #
  # Runtime ID            Circle Stage      #
  # --------------------- ----------------- #
  ( 'osx-x64',            'macos-xcode-9.2' ),
  # --------------------- ----------------- #
]

LINUX = [
  # --------------------- ----------------- #
  # Runtime ID            Circle Stage      #
  # --------------------- ----------------- #
  ( 'linux-x64',          'debian-stretch'  ),
  ( 'alpine.3.6-x64',     'alpine-3.6'      ),
  # --------------------- ----------------- #
]

EXTRAS = [ 'LICENSE', 'AUTHORS', 'ChangeLog' ]

PROPSFILE = 'libsodium.props'
MAKEFILE = 'Makefile'
OUTPUTDIR = 'artifacts'
BUILDDIR = 'build'
CACHEDIR = 'cache'
TEMPDIR = 'temp'

PACKAGE = 'libsodium'
LIBRARY = 'libsodium'

class Version:

  def __init__(self, libsodium_version, package_version):
    self.libsodium_version = libsodium_version
    self.package_version = package_version

    self.builddir = os.path.join(BUILDDIR, libsodium_version)
    self.tempdir = os.path.join(TEMPDIR, libsodium_version)
    self.projfile = os.path.join(self.builddir, '{0}.{1}.pkgproj'.format(PACKAGE, package_version))
    self.propsfile = os.path.join(self.builddir, '{0}.props'.format(PACKAGE))
    self.pkgfile = os.path.join(OUTPUTDIR, '{0}.{1}.nupkg'.format(PACKAGE, package_version))

class WindowsItem:

  def __init__(self, version, rid, platform):
    self.url = 'https://download.libsodium.org/libsodium/releases/libsodium-{0}-msvc.zip'.format(version.libsodium_version)
    self.cachefile = os.path.join(CACHEDIR, re.sub(r'[^A-Za-z0-9.]', '-', self.url))
    self.packfile = os.path.join(version.builddir, 'runtimes', rid, 'native', LIBRARY + '.dll')
    self.itemfile = '{0}/Release/v140/dynamic/libsodium.dll'.format(platform)
    self.tempdir = os.path.join(version.tempdir, rid)
    self.tempfile = os.path.join(self.tempdir, os.path.normpath(self.itemfile))

  def make(self, f):
    f.write('\n')
    f.write('{0}: {1}\n'.format(self.packfile, self.tempfile))
    f.write('\t@mkdir -p $(dir $@)\n')
    f.write('\tcp -f $< $@\n')
    f.write('\n')
    f.write('{0}: {1}\n'.format(self.tempfile, self.cachefile))
    f.write('\t@mkdir -p $(dir $@)\n')
    f.write('\tcd {0} && unzip -q -DD -o {1} \'{2}\'\n'.format(
      self.tempdir,
      os.path.relpath(self.cachefile, self.tempdir),
      self.itemfile
    ))

class MacOSItem:

  def __init__(self, version, rid, circle_stage):
    self.url = 'https://download.libsodium.org/libsodium/releases/libsodium-{0}.tar.gz'.format(version.libsodium_version)
    self.cachefile = os.path.join(CACHEDIR, re.sub(r'[^A-Za-z0-9.]', '-', self.url))
    self.packfile = os.path.join(version.builddir, 'runtimes', rid, 'native', LIBRARY + '.dylib')
    self.inputfile = os.path.join('~', 'workspace', circle_stage, 'libsodium.dylib')

  def make(self, f):
    f.write('\n')
    f.write('{0}: {1}\n'.format(self.packfile, self.inputfile))
    f.write('\t@mkdir -p $(dir $@)\n')
    f.write('\tcp -f $< $@\n')

class LinuxItem:

  def __init__(self, version, rid, circle_stage):
    self.url = 'https://download.libsodium.org/libsodium/releases/libsodium-{0}.tar.gz'.format(version.libsodium_version)
    self.cachefile = os.path.join(CACHEDIR, re.sub(r'[^A-Za-z0-9.]', '-', self.url))
    self.packfile = os.path.join(version.builddir, 'runtimes', rid, 'native', LIBRARY + '.so')
    self.inputfile = os.path.join('~', 'workspace', circle_stage, 'libsodium.so')

  def make(self, f):
    f.write('\n')
    f.write('{0}: {1}\n'.format(self.packfile, self.inputfile))
    f.write('\t@mkdir -p $(dir $@)\n')
    f.write('\tcp -f $< $@\n')

class ExtraItem:

  def __init__(self, version, filename):
    self.url = 'https://download.libsodium.org/libsodium/releases/libsodium-{0}.tar.gz'.format(version.libsodium_version)
    self.cachefile = os.path.join(CACHEDIR, re.sub(r'[^A-Za-z0-9.]', '-', self.url))
    self.packfile = os.path.join(version.builddir, filename)
    self.itemfile = 'libsodium-{0}/{1}'.format(version.libsodium_version, filename)
    self.tempdir = os.path.join(version.tempdir, 'extras')
    self.tempfile = os.path.join(self.tempdir, os.path.normpath(self.itemfile))

  def make(self, f):
    f.write('\n')
    f.write('{0}: {1}\n'.format(self.packfile, self.tempfile))
    f.write('\t@mkdir -p $(dir $@)\n')
    f.write('\tcp -f $< $@\n')
    f.write('\n')
    f.write('{0}: {1}\n'.format(self.tempfile, self.cachefile))
    f.write('\t@mkdir -p $(dir $@)\n')
    f.write('\tcd {0} && tar xzmf {1} \'{2}\'\n'.format(
      self.tempdir,
      os.path.relpath(self.cachefile, self.tempdir),
      self.itemfile
    ))

def main(args):
  m = re.fullmatch(r'((\d+\.\d+\.\d+)(\.\d+)?)(?:-(\w+(?:[_.-]\w+)*))?', args[1]) if len(args) == 2 else None

  if m is None:
    print('Usage:')
    print('       python3 prepare.py <version>')
    print()
    print('Examples:')
    print('       python3 prepare.py 1.0.14-preview-01')
    print('       python3 prepare.py 1.0.14-preview-02')
    print('       python3 prepare.py 1.0.14-preview-03')
    print('       python3 prepare.py 1.0.14')
    print('       python3 prepare.py 1.0.14.1-preview-01')
    print('       python3 prepare.py 1.0.14.1')
    print('       python3 prepare.py 1.0.14.2')
    return 1

  version = Version(m.group(2), m.group(0))

  items = [ WindowsItem(version, rid, platform)   for (rid, platform) in WINDOWS   ] + \
          [ MacOSItem(version, rid, codename)     for (rid, codename) in MACOS     ] + \
          [ LinuxItem(version, rid, docker_image) for (rid, docker_image) in LINUX ] + \
          [ ExtraItem(version, filename)          for filename in EXTRAS           ]

  downloads = {item.cachefile: item.url for item in items}

  with open(MAKEFILE, 'w') as f:
    f.write('all: {0}\n'.format(version.pkgfile))

    for download in sorted(downloads):
      f.write('\n')
      f.write('{0}:\n'.format(download))
      f.write('\t@mkdir -p $(dir $@)\n')
      f.write('\tcurl -fsLo $@ \'{0}\'\n'.format(downloads[download]))

    for item in items:
      item.make(f)

    f.write('\n')
    f.write('{0}: {1}\n'.format(version.propsfile, PROPSFILE))
    f.write('\t@mkdir -p $(dir $@)\n')
    f.write('\tcp -f $< $@\n')

    f.write('\n')
    f.write('{0}: {1}\n'.format(version.projfile, version.propsfile))
    f.write('\t@mkdir -p $(dir $@)\n')
    f.write('\techo \'' +
            '<Project Sdk="Microsoft.NET.Sdk">' +
            '<Import Project="{0}" />'.format(os.path.relpath(version.propsfile, os.path.dirname(version.projfile))) +
            '<PropertyGroup>' +
            '<Version>{0}</Version>'.format(version.package_version) +
            '</PropertyGroup>' +
            '</Project>\' > $@\n')

    f.write('\n')
    f.write('{0}:'.format(version.pkgfile))
    f.write(' \\\n\t\t{0}'.format(version.projfile))
    f.write(' \\\n\t\t{0}'.format(version.propsfile))
    for item in items:
      f.write(' \\\n\t\t{0}'.format(item.packfile))
    f.write('\n')
    f.write('\t@mkdir -p $(dir $@)\n')
    f.write('\tdotnet pack -o {1} {0}\n'.format(version.projfile, os.path.relpath(OUTPUTDIR, version.builddir)))

  print('prepared', MAKEFILE, 'to make', version.pkgfile, 'for libsodium', version.libsodium_version)
  return 0

if __name__ == '__main__':
  sys.exit(main(sys.argv))
