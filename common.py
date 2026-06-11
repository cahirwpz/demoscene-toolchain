#!/usr/bin/env python3
# fmt: off

from fnmatch import fnmatch
from glob import glob
from logging import debug, info, error
from os import path
from pathlib import Path
import contextlib
import os
from multiprocessing import cpu_count
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import requests
import zipfile

VARS = {}


def setvar(**kwargs):
  for key, item in kwargs.items():
    VARS[key] = item.format(**VARS)


def fill_in(value):
  if isinstance(value, str):
    return value.format(**VARS)
  return value


def fill_in_args(fn):
  def wrapper(*args, **kwargs):
    args = list(fill_in(arg) for arg in args)
    kwargs = dict((key, fill_in(value)) for key, value in kwargs.items())
    return fn(*args, **kwargs)
  return wrapper


def flatten(*args):
  queue = list(args)

  while queue:
    item = queue.pop(0)
    if isinstance(item, list):
      queue = item + queue
    elif isinstance(item, tuple):
      queue = list(item) + queue
    else:
      yield item


# Template-expanding wrappers around os.path helpers. We bind new names instead
# of patching os.path, so the stdlib module is left untouched for every other
# importer in the process.
chdir = fill_in_args(os.chdir)
exists = fill_in_args(path.exists)
join = fill_in_args(path.join)
relpath = fill_in_args(path.relpath)


@fill_in_args
def panic(*args):
  error(*args)
  sys.exit(1)


@fill_in_args
def topdir(name):
  if not path.isabs(name):
    name = path.abspath(name)
  return relpath(name, '{top}')


@fill_in_args
def find_executable(name):
  return (shutil.which(name) or
          panic('Executable "%s" not found!', name))


@fill_in_args
def require_packages(*packages):
  """On Debian-based systems, verify required dev packages are installed."""
  if not exists('/etc/debian_version'):
    return
  res = subprocess.run(['dpkg-query', '-W', '-f=${Package} ${Status}\n'] + list(packages),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
  installed = {line.split()[0] for line in res.stdout.splitlines()
               if len(line.split()) >= 4 and line.split()[1:] == ['install', 'ok', 'installed']}
  missing = [p for p in packages if p not in installed]
  if missing:
    panic('Missing packages: %s\nRun: sudo apt-get install %s',
          ' '.join(missing), ' '.join(missing))


@fill_in_args
def find(root, **kwargs):
  only_files = kwargs.get('only_files', False)
  include = kwargs.get('include', ['*'])
  exclude = kwargs.get('exclude', [''])
  lst = []
  for name in sorted(os.listdir(root)):
    fullname = join(root, name)
    is_dir = path.isdir(fullname)
    excluded = any(fnmatch(name, pat) for pat in exclude)
    included = any(fnmatch(name, pat) for pat in include)
    if included and not excluded:
      if not (is_dir and only_files):
        lst.append(fullname)
    if is_dir and not excluded:
      lst.extend(find(fullname, **kwargs))
  return lst


@fill_in_args
def touch(name):
  Path(name).touch(exist_ok=True)


@fill_in_args
def mkdtemp(**kwargs):
  if 'dir' in kwargs and not path.isdir(kwargs['dir']):
    mkdir(kwargs['dir'])
  return tempfile.mkdtemp(**kwargs)


@fill_in_args
def mkstemp(**kwargs):
  if 'dir' in kwargs and not path.isdir(kwargs['dir']):
    mkdir(kwargs['dir'])
  return tempfile.mkstemp(**kwargs)


@fill_in_args
def rmtree(*names):
  for name in flatten(names):
    p = Path(name)
    if p.is_dir():
      debug('rmtree "%s"', topdir(name))
      shutil.rmtree(p)


@fill_in_args
def remove(*names):
  for name in flatten(names):
    p = Path(name)
    if p.is_file():
      debug('remove "%s"', topdir(name))
      p.unlink()


@fill_in_args
def mkdir(*names):
  for name in flatten(names):
    if name:
      Path(name).mkdir(parents=True, exist_ok=True)


@fill_in_args
def copy(src, dst):
  debug('copy "%s" to "%s"', topdir(src), topdir(dst))
  shutil.copy2(src, dst)


@fill_in_args
def copytree(src, dst, **kwargs):
  debug('copytree "%s" to "%s"', topdir(src), topdir(dst))

  mkdir(dst)

  for name in find(src, **kwargs):
    target = join(dst, relpath(name, src))
    if path.isdir(name):
      mkdir(target)
    else:
      copy(name, target)


@fill_in_args
def move(src, dst):
  debug('move "%s" to "%s"', topdir(src), topdir(dst))
  shutil.move(src, dst)


@fill_in_args
def symlink(src, name):
  p = Path(name)
  if not p.is_symlink():
    debug('symlink "%s" points at "%s"', topdir(name), src)
    p.symlink_to(src)


@fill_in_args
def chmod(name, mode):
  debug('change permissions on "%s" to "%o"', topdir(name), mode)
  os.chmod(name, mode)


@fill_in_args
def execute(*cmd, **kwargs):
  debug('execute "%s"', " ".join(cmd))
  ignore_errors = kwargs.get('ignore_errors', False)
  try:
    subprocess.run(cmd, check=True)
  except subprocess.CalledProcessError as ex:
    if not ignore_errors:
      panic('command "%s" failed with %d',
            " ".join(list(ex.cmd)), ex.returncode)


@fill_in_args
def textfile(*lines):
  f, name = mkstemp(dir='{tmpdir}')
  debug('creating text file script "%s"', topdir(name))
  os.write(f, ('\n'.join(lines) + '\n').encode())
  os.close(f)
  return name


DOWNLOAD_TIMEOUT = (15, 60)  # (connect, read) seconds
DOWNLOAD_RETRIES = 3


@fill_in_args
def download(url, name):
  info('download "%s" to "%s"', url, topdir(name))

  for attempt in range(1, DOWNLOAD_RETRIES + 1):
    try:
      _download_once(url, name)
      return
    except requests.exceptions.RequestException as ex:
      if attempt == DOWNLOAD_RETRIES:
        # Leave no truncated file behind: fetch() treats an existing file as
        # "already downloaded", so a partial file would be mistaken for complete.
        remove(name)
        panic('download of "%s" failed after %d attempts: %s',
              url, DOWNLOAD_RETRIES, ex)
      delay = 2 ** attempt
      info('download attempt %d/%d failed (%s); retrying in %ds',
           attempt, DOWNLOAD_RETRIES, ex, delay)
      time.sleep(delay)


def _download_once(url, name):
  res = requests.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT)
  res.raise_for_status()

  try:
    size = int(res.headers.get('content-length', ''))
  except (ValueError, TypeError):
    size = None

  if size:
    info('download: %s (size: %d)', name, size)
  else:
    info('download: %s', name)

  is_tty = sys.stdout.isatty()
  with open(name, 'wb') as f:
    done = 0
    last_reported = 0
    for chunk in res.iter_content(chunk_size=8192):
      if not chunk:
        continue
      done += len(chunk)
      f.write(chunk)
      if is_tty:
        status = f'\r{done} [{done * 100. / size:.2f}%]' if size else f'\r{done} bytes'
        sys.stdout.write(status)
        sys.stdout.flush()
      elif done - last_reported >= 5 * 1024 * 1024 or (size and done == size):
        if size:
          info('downloading %s: %3.2f%% (%d/%d bytes)', name, done * 100. / size, done, size)
        else:
          info('downloading %s: %d bytes', name, done)
        last_reported = done

  if is_tty:
    print('')


# tarfile gained the 'data' extraction filter in 3.12 (backported to 3.8.17+);
# detect it so we can also run on the 3.11 image without a hard dependency.
_HAVE_TAR_FILTER = hasattr(tarfile, 'data_filter')


def _within_dir(base, target):
  base = path.realpath(base)
  target = path.realpath(target)
  return target == base or target.startswith(base + os.sep)


@fill_in_args
def unarc(name):
  info('extract files from "%s"', topdir(name))

  if name.endswith('.lha'):
    import lhafile
    arc = lhafile.LhaFile(name)
    for item in arc.infolist():
      filename = os.sep.join(item.filename.split('\\'))
      mkdir(path.dirname(filename))
      debug('extract "%s"', filename)
      if path.isdir(filename):
        continue
      with open(filename, 'wb') as f:
        f.write(arc.read(item.filename))
  elif name.endswith('.tar.gz') or name.endswith('.tar.bz2'):
    dest = os.getcwd()
    with tarfile.open(name) as arc:
      for item in arc.getmembers():
        debug('extract "%s"', item.name)
        if not _within_dir(dest, join(dest, item.name)):
          panic('refusing unsafe path "%s" in archive "%s"', item.name, topdir(name))
        if _HAVE_TAR_FILTER:
          arc.extract(item, filter='data')
        else:
          arc.extract(item)
  elif name.endswith('.zip'):
    dest = os.getcwd()
    with zipfile.ZipFile(name) as arc:
      for item in arc.infolist():
        debug('extract "%s"', item.filename)
        if not _within_dir(dest, join(dest, item.filename)):
          panic('refusing unsafe path "%s" in archive "%s"', item.filename, topdir(name))
        arc.extract(item)
  else:
    raise RuntimeError('Unrecognized archive: "%s"', name)


@contextlib.contextmanager
def cwd(name):
  old = os.getcwd()
  if not exists(name):
    mkdir(name)
  try:
    debug('enter directory "%s"', topdir(name))
    chdir(name)
    yield
  finally:
    chdir(old)


@contextlib.contextmanager
def env(**kwargs):
  backup = {}
  try:
    for key, value in kwargs.items():
      debug('changing environment variable "%s" to "%s"', key, value)
      old = os.environ.get(key, None)
      os.environ[key] = fill_in(value)
      backup[key] = old
    yield
  finally:
    for key, value in backup.items():
      debug('restoring old value of environment variable "%s"', key)
      if value is None:
        del os.environ[key]
      else:
        os.environ[key] = value


def recipe(name, nargs=0):
  def real_decorator(fn):
    @fill_in_args
    def wrapper(*args, **kwargs):
      target = [str(arg) for arg in args[:min(nargs, len(args))]]
      if len(target) > 0:
        target = [target[0], fill_in(name)] + target[1:]
        target = '-'.join(target)
      else:
        target = fill_in(name)
      target = target.replace('_', '-')
      target = target.replace('/', '-')
      stamp = join('{stamps}', target)
      if not exists('{stamps}'):
        mkdir('{stamps}')
      if not exists(stamp):
        fn(*args, **kwargs)
        touch(stamp)
      else:
        info('already done "%s"', target)
    return wrapper
  return real_decorator


@recipe('fetch', 1)
def fetch(name, url):
  if url.startswith('http') or url.startswith('ftp'):
    if not exists(name):
      download(url, name)
    else:
      info('File "%s" already downloaded.', name)
  elif url.startswith('svn'):
    execute('svn', 'export', url, name)
  elif url.startswith('git'):
    if not exists(name):
      execute('git', 'clone', url, name)
    else:
      with cwd(name):
        execute('git', 'pull')
  elif url.startswith('file'):
    if not exists(name):
      _, src = url.split('://')
      copy(src, name)
  else:
    panic('URL "%s" not recognized!', url)


@recipe('unpack', 1)
def unpack(name, work_dir='{sources}', top_dir=None, dst_dir=None):
  try:
    src = (glob(join('{archives}', name) + '*') +
           glob(join('{submodules}', name) + '*'))[0]
  except IndexError:
    src = ""
    panic('Missing files for "%s".', name)

  dst = join(work_dir, dst_dir or name)

  info('preparing files for "%s"', name)

  if path.isdir(src):
    if top_dir is not None:
      src = join(src, top_dir)
    copytree(src, dst, exclude=['.svn', '.git'])
  else:
    tmpdir = mkdtemp(dir='{tmpdir}')
    with cwd(tmpdir):
      unarc(src)
    copytree(join(tmpdir, top_dir or name), dst)
    rmtree(tmpdir)


@recipe('patch', 1)
def patch(name, work_dir='{sources}'):
  with cwd(work_dir):
    for name in find(join('{patches}', name),
                     only_files=True, exclude=['*~']):
      if fnmatch(name, '*.diff'):
        execute('patch', '-t', '-p0', '-i', name)
      else:
        dst = relpath(name, '{patches}')
        mkdir(path.dirname(dst))
        copy(name, dst)


@recipe('configure', 1)
def configure(name, *confopts, **kwargs):
  info('configuring "%s"', name)

  if 'from_dir' in kwargs:
    from_dir = kwargs['from_dir']
  else:
    from_dir = join('{sources}', name)

  if kwargs.get('copy_source', False):
    rmtree(join('{build}', name))
    copytree(join('{sources}', name), join('{build}', name))
    from_dir = '.'

  with cwd(join('{build}', name)):
    remove(find('.', include=['config.cache']))
    execute(join(from_dir, 'configure'), *confopts)


@recipe('make', 2)
def make(name, target=None, makefile=None, parallel=False, **makevars):
  info('running make "%s"', target)

  with cwd(join('{build}', name)):
    args = ['%s=%s' % item for item in makevars.items()]
    if target is not None:
      args = [target] + args
    if makefile is not None:
      args = ['-f', makefile] + args
    if parallel:
      args = ['-j%d' % min(8, cpu_count())] + args
    execute('make', *args)


def require_header(headers, lang='c', errmsg='', symbol=None, value=None):
  debug('require_header "%s"', headers[0])

  for header in headers:
    cmd = {'c': os.environ['CC'], 'c++': os.environ['CXX']}[lang]
    cmd = fill_in(cmd).split()
    opts = ['-fsyntax-only', '-x', lang, '-']
    proc_stdin = ['#include <%s>' % header]
    if symbol:
      if value:
        proc_stdin.append("#if %s != %s" % (symbol, value))
      else:
        proc_stdin.append("#ifndef %s" % symbol)
        proc_stdin.append("#error")
        proc_stdin.append("#endif")

    res = subprocess.run(cmd + opts, input='\n'.join(proc_stdin), text=True, capture_output=True)
    if res.returncode == 0:
      return

  panic(errmsg)


__all__ = ['setvar', 'panic', 'find_executable', 'chmod', 'execute', 'rmtree',
           'mkdir', 'copy', 'copytree', 'fetch', 'cwd', 'symlink', 'remove',
           'move', 'find', 'textfile', 'env', 'path', 'recipe', 'unpack',
           'patch', 'configure', 'make', 'require_header', 'require_packages',
           'touch', 'exists', 'join', 'relpath']
