#!/usr/bin/env python3

# Build cross toolchain for AmigaOS <= 3.9 / M68k target.

from fnmatch import fnmatch
from glob import glob
from logging import info, getLogger
from os import environ
import argparse
import logging
import platform
import sys

environ['DONTWRITEBYTECODE'] = 'y'

URLS = \
  ['https://ftp.gnu.org/gnu/m4/m4-1.4.17.tar.gz',
   'https://ftp.gnu.org/gnu/gawk/gawk-3.1.8.tar.gz',
   'https://ftp.gnu.org/gnu/autoconf/autoconf-2.13.tar.gz',
   'https://ftp.gnu.org/gnu/bison/bison-1.35.tar.gz',
   'https://ftp.gnu.org/gnu/texinfo/texinfo-4.12.tar.gz',
   'https://ftp.gnu.org/gnu/automake/automake-1.15.tar.gz',
   'https://gcc.gnu.org/pub/gcc/infrastructure/gmp-6.2.1.tar.bz2',
   'https://gcc.gnu.org/pub/gcc/infrastructure/mpfr-3.1.6.tar.bz2',
   'https://gcc.gnu.org/pub/gcc/infrastructure/mpc-1.0.3.tar.gz',
   'https://gcc.gnu.org/pub/gcc/infrastructure/isl-0.18.tar.bz2',
   ('https://github.com/askeksa/Shrinkler/archive/refs/tags/v4.7.tar.gz',
    'Shrinkler-4.7.tar.gz'),
   ('https://github.com/emmanuel-marty/salvador/archive/refs/tags/1.4.2.tar.gz',
    'salvador-1.4.2.tar.gz'),
   ('https://github.com/emmanuel-marty/lzsa/archive/refs/tags/1.4.1.tar.gz',
    'lzsa-1.4.1.tar.gz'),
   'https://ftp.gnu.org/old-gnu/gnu-0.2/src/flex-2.5.4.tar.gz',
   ('http://hp.alinea-computer.de/AmigaOS/NDK39.lha', 'NDK_3.9.lha'),
   ('http://phoenix.owl.de/tags/vasm1_9c.tar.gz', 'vasm.tar.gz')]


from common import (setvar, execute, rmtree, configure, unpack, path, panic,
        mkdir, env, make, touch, patch, require_header, copy, cwd, recipe,
        find_executable, textfile, chmod, copytree, move, find, fetch)


@recipe('target-prepare')
def prepare_target():
  info('preparing target')

  with cwd('{prefix}'):
    mkdir('bin', 'etc', '{target}')
  with cwd('{prefix}/{target}'):
    mkdir('bin', 'ndk/include/inline', 'ndk/include/lvo',
          'ndk/lib', 'ndk/lib/fd', 'ndk/lib/sfd')


@recipe('vasm-install')
def install_vasm():
  info('installing vasm')

  copy('{build}/vasm/vasmm68k_mot', '{prefix}/{target}/bin')
  vasm = textfile(
    '#!/bin/sh',
    '',
    '{prefix}/{target}/bin/vasmm68k_mot -I{prefix}/{target}/ndk/include "$@"')
  chmod(vasm, 0o755)
  move(vasm, '{prefix}/bin/vasm')


@recipe('{NDK}-install')
def install_ndk():
  info('installing ndk')

  copytree('{sources}/{NDK}/Include/include_h', '{prefix}/{target}/ndk/include')
  copytree('{sources}/{NDK}/Include/include_i', '{prefix}/{target}/ndk/include')
  copytree('{sources}/{NDK}/Include/fd', '{prefix}/{target}/ndk/lib/fd')
  copytree('{sources}/{NDK}/Include/sfd', '{prefix}/{target}/ndk/lib/sfd')
  copytree('{sources}/{NDK}/Include/linker_libs', '{prefix}/{target}/ndk/lib',
           exclude=['README'])
  copytree('{sources}/{NDK}/Documentation/Autodocs', '{prefix}/{target}/ndk/doc')

  for name in find('{prefix}/{target}/ndk/lib/sfd', include=['*.sfd']):
    base = path.basename(name).split('_')[0]

    execute('sfdc', '--target=m68k-amigaos', '--mode=proto',
            '--output={prefix}/{target}/ndk/include/proto/%s.h' % base, name)
    execute('sfdc', '--target=m68k-amigaos', '--mode=macros',
            '--output={prefix}/{target}/ndk/include/inline/%s.h' % base, name)
    execute('sfdc', '--target=m68k-amigaos', '--mode=lvo',
            '--output={prefix}/{target}/ndk/include/lvo/%s_lib.i' % base, name)


@recipe('fd2sfd-install')
def install_fd2sfd():
  info('installing fd2sfd')

  copy('{build}/fd2sfd/fd2sfd', '{prefix}/bin')
  copy('{build}/fd2sfd/cross/share/{target}/alib.h',
       '{prefix}/{target}/ndk/include/inline')


@recipe('fd2pragma-install')
def install_fd2pragma():
  info('installing fd2pragma')

  copy('{build}/fd2pragma/fd2pragma', '{prefix}/bin')
  for header in ['macros.h', 'stubs.h']:
      copy(path.join('{build}/fd2pragma/Include/inline', header),
           '{prefix}/{target}/ndk/include/inline')


@recipe('shrinkler-install')
def install_shrinkler():
  info('installing shrinkler')

  copy('{build}/{shrinkler}/build/native/Shrinkler', '{prefix}/bin/Shrinkler')


@recipe('salvador-install')
def install_salvador():
  info('installing salvador')

  copy('{build}/{salvador}/salvador', '{prefix}/bin/salvador')


@recipe('lzsa-install')
def install_lzsa():
  info('installing lzsa')

  copy('{build}/{lzsa}/lzsa', '{prefix}/bin/lzsa')


@recipe('fs-uae-bootstrap')
def fs_uae_bootstrap():
  info('bootstrapping fs-uae')

  with cwd('{submodules}/{fsuae}'):
    execute('sh', 'bootstrap')


def update_autotools(dst):
  copy('{sources}/{automake}/lib/config.guess', path.join(dst, 'config.guess'))
  copy('{sources}/{automake}/lib/config.sub', path.join(dst, 'config.sub'))


def touch_genfiles(dst):
  """
  For binutils and gcc we want to make sure C source & headers file doesn't get
  regenerated. Otherwise it can cause weird errors later in the build process
  (e.g. in ldexp.c:560)
  """
  for name in find(dst, include=['*.l', '*.y']):
    basename = path.splitext(name)[0]
    for c_file in glob(basename + '.c'):
      touch(c_file)
    for h_file in glob(basename + '.h'):
      touch(h_file)


def download():
  with cwd('{archives}'):
    for url in URLS:
      if type(url) is tuple:
        url, name = url[0], url[1]
      else:
        name = path.basename(url)
      fetch(name, url)

  execute('git', 'submodule', 'init');
  execute('git', 'submodule', 'update');


def build():
  for var in list(environ.keys()):
    if var not in ['_', 'LOGNAME', 'HOME', 'SHELL', 'TMPDIR', 'PWD']:
      del environ[var]

  PATHS = ['/usr/bin', '/bin']

  """
  Make sure we always choose known compiler (from the distro) and not one in
  user's path that could shadow the original one.
  """
  if platform.system() == 'Darwin':
    CC, CXX = 'clang', 'clang++'
    PATHS.append('/usr/local/bin')
    PATHS.append('/usr/local/opt/gettext/bin')
  else:
    CC, CXX = 'gcc', 'g++'

  if fnmatch(platform.system(), 'MSYS_NT*'):
    PATHS.append('/usr/bin/core_perl')  # pod2text, pod2man

  PATH = ':'.join(PATHS)

  environ['PATH'] = PATH
  environ['LANG'] = 'C'
  environ['TERM'] = 'xterm'

  CC = find_executable(CC)
  CXX = find_executable(CXX)
  FLAGS = '-s -O2 -pipe'

  if getLogger().isEnabledFor(logging.DEBUG):
    FLAGS += ' -Wall'
  else:
    FLAGS += ' -w'
    environ['MAKEFLAGS'] = '--silent'

  environ['CC'] = CC
  environ['CXX'] = CXX
  environ['PATH'] = ':'.join([path.join('{prefix}', 'bin'),
                              path.join('{host}', 'bin'),
                              PATH])

  setvar(cc=environ['CC'], cxx=environ['CXX'])

  """
  When we have a working compiler in our path, we shoule also check if the
  required programs, headers and libraries are present.
  """

  find_executable('perl')
  find_executable('pod2text')
  find_executable('pod2man')
  find_executable('gperf')
  find_executable('patch')
  find_executable('make')
  find_executable('makeinfo')
  find_executable('git')
  find_executable('yacc')

  require_header(['ncurses.h', 'ncurses/ncurses.h'],
                 lang='c', errmsg='libncurses-dev package missing')

  download()
  execute('quilt', 'push', '-a', ignore_errors=True)

  unpack('{automake}')

  unpack('{m4}')
  patch('{m4}')
  configure('{m4}', '--prefix={host}')
  make('{m4}', parallel=True)
  make('{m4}', 'install')

  unpack('{gawk}')
  update_autotools('{sources}/{gawk}')
  patch('{gawk}')
  configure('{gawk}', '--prefix={host}')
  make('{gawk}', parallel=True)
  make('{gawk}', 'install')

  unpack('{flex}')
  patch('{flex}')
  configure('{flex}', '--prefix={host}')
  make('{flex}')
  make('{flex}', 'install')

  unpack('{bison}')
  update_autotools('{sources}/{bison}/config')
  patch('{bison}')
  configure('{bison}', '--prefix={host}')
  make('{bison}', parallel=True)
  make('{bison}', 'install')

  unpack('{texinfo}')
  patch('{texinfo}')
  update_autotools('{sources}/{texinfo}/build-aux')
  configure('{texinfo}', '--prefix={host}')
  make('{texinfo}', parallel=True)
  make('{texinfo}', 'install')

  unpack('{autoconf}')
  update_autotools('{sources}/{autoconf}')
  configure('{autoconf}', '--prefix={host}')
  make('{autoconf}', parallel=True)
  make('{autoconf}', 'install')

  unpack('{gmp}')
  configure('{gmp}',
            '--prefix={host}',
            '--disable-shared',
            '--enable-static')
  make('{gmp}', parallel=True)
  make('{gmp}', 'install')

  unpack('{mpfr}')
  configure('{mpfr}',
            '--prefix={host}',
            '--with-gmp={host}',
            '--disable-shared',
            '--enable-static')
  make('{mpfr}', parallel=True)
  make('{mpfr}', 'install')

  unpack('{mpc}')
  configure('{mpc}',
            '--prefix={host}',
            '--with-gmp={host}',
            '--with-mpfr={host}',
            '--disable-shared',
            '--enable-static')
  make('{mpc}', parallel=True)
  make('{mpc}', 'install')

  unpack('{isl}')
  configure('{isl}',
            '--prefix={host}',
            '--with-gmp-prefix={host}',
            '--disable-shared',
            '--enable-static')
  make('{isl}', parallel=True)
  make('{isl}', 'install')

  prepare_target()

  unpack('vasm', work_dir='{build}')
  make('vasm', CPU='m68k', SYNTAX='mot')
  install_vasm()

  update_autotools('{submodules}/fd2sfd')
  unpack('fd2sfd', work_dir='{build}')
  configure('fd2sfd', '--prefix={prefix}', from_dir='{build}/fd2sfd')
  make('fd2sfd')
  install_fd2sfd()

  unpack('fd2pragma', work_dir='{build}')
  make('fd2pragma')
  install_fd2pragma()

  unpack('sfdc')
  configure('sfdc', '--prefix={prefix}', copy_source=True)
  make('sfdc')
  make('sfdc', 'install')

  unpack('{NDK}')
  patch('{NDK}')
  install_ndk()

  with env(CC=CC, CXX=CXX, CFLAGS=FLAGS, CXXFLAGS=FLAGS, PATH=PATH):
    configure('{binutils}',
              '--prefix={prefix}',
              '--infodir={prefix}/{target}/info',
              '--mandir={prefix}/share/man',
              '--disable-nls',
              '--disable-plugins',
              '--disable-werror',
              '--disable-tui',
              '--with-libgmp-prefix={host}',
              '--with-python=' + sys.executable,
              '--target=m68k-amigaos',
              from_dir='{submodules}/{binutils}')
    touch_genfiles('{submodules}/{binutils}')
    make('{binutils}', 'configure-gdb')
    make('{binutils}', 'all-bfd', parallel=True)
    make('{binutils}', 'all-binutils', parallel=True)
    make('{binutils}', 'all-gas', parallel=True)
    make('{binutils}', 'all-ld', parallel=True)
    make('{binutils}', 'all-gdb', parallel=True)
    make('{binutils}', 'install-binutils')
    make('{binutils}', 'install-gas')
    make('{binutils}', 'install-ld')
    make('{binutils}', 'install-gdb')

  CCOLD = ' '.join([CC, '-std=gnu99'])
  CXXOLD = ' '.join([CXX, '-std=gnu++11'])

  with env(CC=CCOLD, CXX=CXXOLD, CFLAGS=FLAGS, CXXFLAGS=FLAGS):
    configure('{gcc}',
              '--prefix={prefix}',
              '--infodir={prefix}/{target}/info',
              '--mandir={prefix}/share/man',
              '--host=i686-linux-gnu',
              '--build=i686-linux-gnu',
              '--target=m68k-amigaos',
              '--enable-languages=c',
              '--enable-version-specific-runtime-libs',
              from_dir='{submodules}/{gcc}')
    touch_genfiles('{submodules}/{gcc}')
    touch('{submodules}/{gcc}/gcc/c-parse.gperf')
    touch('{submodules}/{gcc}/gcc/configure')
    # parallel build fails for all-gcc
    make('{gcc}', 'all-gcc', MAKEINFO='makeinfo')
    make('{gcc}', 'install-gcc', MAKEINFO='makeinfo')

  with env(CC=CC, CXX=CXX, CFLAGS=FLAGS, CXXFLAGS=FLAGS):
    configure('{gcc_bebbo}',
              '--prefix={prefix}',
              '--infodir={prefix}/{target}/info',
              '--mandir={prefix}/share/man',
              '--program-prefix=m68k-amigaos-',
              '--program-suffix=-6.5.0b',
              '--with-gmp={host}',
              '--with-mpfr={host}',
              '--with-mpc={host}',
              '--with-isl={host}',
              '--target=m68k-amigaos',
              '--enable-languages=c',
              '--enable-version-specific-runtime-libs',
              '--disable-nls',
              '--disable-libssp',
              from_dir='{submodules}/{gcc_bebbo}')
    make('{gcc_bebbo}', 'all-gcc', parallel=True)
    make('{gcc_bebbo}', 'install-gcc')

  with env(CC=CC, CXX=CXX, CFLAGS=FLAGS, CXXFLAGS=FLAGS, PATH=PATH):
    fs_uae_bootstrap()
    configure('{fsuae}',
              '--prefix={prefix}',
              '--enable-gdbstub',
              '--without-libmpeg2',
              '--disable-action-replay',
              '--disable-ahi',
              '--disable-builtin-slirp',
              '--disable-gfxboard',
              '--disable-jit',
              '--disable-lua',
              '--disable-netplay',
              '--disable-pearpc-cpu',
              '--disable-ppc',
              '--disable-prowizard',
              '--disable-slirp',
              '--disable-qemu-cpu',
              '--disable-qemu-slirp',
              '--disable-uaescsi',
              '--disable-uaeserial',
              '--disable-dms',
              '--disable-zip',
              from_dir='{submodules}/{fsuae}')
    make('{fsuae}', parallel=True)
    make('{fsuae}', 'install')

  unpack('{shrinkler}', work_dir='{build}')
  make('{shrinkler}')
  install_shrinkler()

  unpack('{salvador}', work_dir='{build}')
  make('{salvador}', CC='gcc')
  install_salvador()

  unpack('{lzsa}', work_dir='{build}')
  make('{lzsa}', CC='gcc')
  install_lzsa()


def clean():
  rmtree('{stamps}')
  rmtree('{sources}')
  rmtree('{host}')
  rmtree('{build}')
  rmtree('{tmpdir}')
  execute('quilt', 'pop', '-a', ignore_errors=True)


if __name__ == "__main__":
  logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

  if not sys.version_info[:2] >= (3, 5):
    panic('I need Python 3.5 to run!')

  if not any(fnmatch(platform.system(), pat)
             for pat in ['Darwin', 'Linux', 'CYGWIN_NT*', 'MSYS_NT*']):
    panic('Build on %s not supported!', platform.system())

  if platform.machine() not in ['i686', 'x86_64']:
    panic('Build on %s architecture not supported!', platform.machine())

  parser = argparse.ArgumentParser(description='Build cross toolchain.')
  parser.add_argument('action',
                      choices=['build', 'clean', 'download'],
                      default='build', help='perform action')
  parser.add_argument('args', metavar='ARGS', type=str, nargs='*',
                      help='action arguments')
  parser.add_argument('-q', '--quiet', action='store_true')
  parser.add_argument('--prefix', type=str, default=None,
                      help='installation directory')
  args = parser.parse_args()

  setvar(top=path.abspath(path.dirname(sys.argv[0])))

  setvar(m4='m4-1.4.17',
         gawk='gawk-3.1.8',
         flex='flex-2.5.4',
         bison='bison-1.35',
         automake='automake-1.15',
         autoconf='autoconf-2.13',
         texinfo='texinfo-4.12',
         gmp='gmp-6.2.1',
         mpfr='mpfr-3.1.6',
         mpc='mpc-1.0.3',
         isl='isl-0.18',
         NDK='NDK_3.9',
         binutils='binutils-gdb',
         fsuae='fs-uae',
         gcc='gcc-2.95.3',
         gcc_bebbo='gcc-bebbo',
         shrinkler='Shrinkler-4.7',
         salvador='salvador-1.4.2',
         lzsa='lzsa-1.4.1',
         target='m68k-amigaos',
         python=sys.executable,
         patches=path.join('{top}', 'patches'),
         stamps=path.join('{top}', '.build-m68k', 'stamps'),
         build=path.join('{top}', '.build-m68k', 'build'),
         sources=path.join('{top}', '.build-m68k', 'sources'),
         host=path.join('{top}', '.build-m68k', 'host'),
         tmpdir=path.join('{top}', '.build-m68k', 'tmp'),
         prefix=path.join('{top}', 'm68k-amigaos'),
         archives=path.join('{top}', '.build-m68k', 'archives'),
         submodules=path.join('{top}', 'submodules'))

  if args.quiet:
    getLogger().setLevel(logging.INFO)

  if args.prefix is not None:
    setvar(prefix=args.prefix)

  if not path.exists('{prefix}'):
    mkdir('{prefix}')

  action = args.action.replace('-', '_')
  globals()[action].__call__(*args.args)
