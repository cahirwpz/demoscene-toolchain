#!/usr/bin/env python3 -B

from fnmatch import fnmatch
from glob import glob
from logging import debug, info, error
from os import path
import contextlib
import os
from multiprocessing import cpu_count
import shutil
import subprocess
import sys
import tarfile
import tempfile
from urllib.request import urlopen
import zipfile

VARS = {}


def setvar(**kwargs):
  for key, item in kwargs.items():
    VARS[key] = item.format(**VARS)


def fill_in(value):
  if type(value) is str:
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
    if type(item) is list:
      queue = item + queue
    elif type(item) is tuple:
      queue = list(item) + queue
    else:
      yield item


chdir = fill_in_args(os.chdir)
path.exists = fill_in_args(path.exists)
path.join = fill_in_args(path.join)
path.relpath = fill_in_args(path.relpath)


@fill_in_args
def panic(*args):
  error(*args)
  sys.exit(1)


@fill_in_args
def topdir(name):
  if not path.isabs(name):
    name = path.abspath(name)
  return path.relpath(name, '{top}')


@fill_in_args
def find_executable(name):
  return (shutil.which(name) or
          panic('Executable "%s" not found!', name))


@fill_in_args
def find(root, **kwargs):
  only_files = kwargs.get('only_files', False)
  include = kwargs.get('include', ['*'])
  exclude = kwargs.get('exclude', [''])
  lst = []
  for name in sorted(os.listdir(root)):
    fullname = path.join(root, name)
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
  try:
    os.utime(name, None)
  except OSError:
    open(name, 'a').close()


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
    if path.isdir(name):
      debug('rmtree "%s"', topdir(name))
      shutil.rmtree(name)


@fill_in_args
def remove(*names):
  for name in flatten(names):
    if path.isfile(name):
      debug('remove "%s"', topdir(name))
      os.remove(name)


@fill_in_args
def mkdir(*names):
  for name in flatten(names):
    if name and not path.isdir(name):
      debug('makedir "%s"', topdir(name))
      os.makedirs(name)


@fill_in_args
def copy(src, dst):
  debug('copy "%s" to "%s"', topdir(src), topdir(dst))
  shutil.copy2(src, dst)


@fill_in_args
def copytree(src, dst, **kwargs):
  debug('copytree "%s" to "%s"', topdir(src), topdir(dst))

  mkdir(dst)

  for name in find(src, **kwargs):
    target = path.join(dst, path.relpath(name, src))
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
  if not path.islink(name):
    debug('symlink "%s" points at "%s"', topdir(name), src)
    os.symlink(src, name)


@fill_in_args
def chmod(name, mode):
  debug('change permissions on "%s" to "%o"', topdir(name), mode)
  os.chmod(name, mode)


@fill_in_args
def execute(*cmd, **kwargs):
  debug('execute "%s"', " ".join(cmd))
  ignore_errors = kwargs.get('ignore_errors', False)
  try:
    subprocess.check_call(cmd)
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


@fill_in_args
def download(url, name):
  info('download "%s" to "%s"', url, topdir(name))

  u = urlopen(url)
  meta = u.info()
  try:
    size = int(meta['Content-Length'])
  except (IndexError, TypeError):
    size = None

  if size:
    info('download: %s (size: %d)', name, size)
  else:
    info('download: %s', name)

  with open(name, 'wb') as f:
    done = 0
    block = 8192
    while True:
      buf = u.read(block)
      if not buf:
        break
      done += len(buf)
      f.write(buf)
      if size:
        status = r"%d [%3.2f%%]" % (done, done * 100. / size)
      else:
        status = r"%d" % done
      status = status + chr(8) * (len(status) + 1)
      sys.stdout.write(status)
      sys.stdout.flush()

  print("")


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
    with tarfile.open(name) as arc:
      for item in arc.getmembers():
        debug('extract "%s"' % item.name)
        arc.extract(item)
  elif name.endswith('.zip'):
    with zipfile.ZipFile(name) as arc:
      for item in arc.infolist():
        debug('extract "%s"' % item.filename)
        arc.extract(item)
  else:
    raise RuntimeError('Unrecognized archive: "%s"', name)


@contextlib.contextmanager
def cwd(name):
  old = os.getcwd()
  if not path.exists(name):
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
      stamp = path.join('{stamps}', target)
      if not path.exists('{stamps}'):
        mkdir('{stamps}')
      if not path.exists(stamp):
        fn(*args, **kwargs)
        touch(stamp)
      else:
        info('already done "%s"', target)
    return wrapper
  return real_decorator


@recipe('fetch', 1)
def fetch(name, url):
  if url.startswith('http') or url.startswith('ftp'):
    if not path.exists(name):
      download(url, name)
    else:
      info('File "%s" already downloaded.', name)
  elif url.startswith('svn'):
    execute('svn', 'export', url, name)
  elif url.startswith('git'):
    if not path.exists(name):
      execute('git', 'clone', url, name)
    else:
      with cwd(name):
        execute('git', 'pull')
  elif url.startswith('file'):
    if not path.exists(name):
      _, src = url.split('://')
      copy(src, name)
  else:
    panic('URL "%s" not recognized!', url)


@recipe('unpack', 1)
def unpack(name, work_dir='{sources}', top_dir=None, dst_dir=None):
  try:
    src = (glob(path.join('{archives}', name) + '*') +
           glob(path.join('{submodules}', name) + '*'))[0]
  except IndexError:
    src = ""
    panic('Missing files for "%s".', name)

  dst = path.join(work_dir, dst_dir or name)

  info('preparing files for "%s"', name)

  if path.isdir(src):
    if top_dir is not None:
      src = path.join(src, top_dir)
    copytree(src, dst, exclude=['.svn', '.git'])
  else:
    tmpdir = mkdtemp(dir='{tmpdir}')
    with cwd(tmpdir):
      unarc(src)
    copytree(path.join(tmpdir, top_dir or name), dst)
    rmtree(tmpdir)


@recipe('patch', 1)
def patch(name, work_dir='{sources}'):
  with cwd(work_dir):
    for name in find(path.join('{patches}', name),
                     only_files=True, exclude=['*~']):
      if fnmatch(name, '*.diff'):
        execute('patch', '-t', '-p0', '-i', name)
      else:
        dst = path.relpath(name, '{patches}')
        mkdir(path.dirname(dst))
        copy(name, dst)


@recipe('configure', 1)
def configure(name, *confopts, **kwargs):
  info('configuring "%s"', name)

  if 'from_dir' in kwargs:
    from_dir = kwargs['from_dir']
  else:
    from_dir = path.join('{sources}', name)

  if kwargs.get('copy_source', False):
    rmtree(path.join('{build}', name))
    copytree(path.join('{sources}', name), path.join('{build}', name))
    from_dir = '.'

  with cwd(path.join('{build}', name)):
    remove(find('.', include=['config.cache']))
    execute(path.join(from_dir, 'configure'), *confopts)


@recipe('make', 2)
def make(name, target=None, makefile=None, parallel=False, **makevars):
  info('running make "%s"', target)

  with cwd(path.join('{build}', name)):
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
    proc = subprocess.Popen(cmd + opts,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    proc_stdin = ['#include <%s>' % header]
    if symbol:
      if value:
        proc_stdin.append("#if %s != %s" % (symbol, value))
      else:
        proc_stdin.append("#ifndef %s" % symbol)
        proc_stdin.append("#error")
        proc_stdin.append("#endif")

    _, _ = proc.communicate('\n'.join(proc_stdin).encode())
    proc.wait()

    if proc.returncode == 0:
      return

  panic(errmsg)


__all__ = ['setvar', 'panic', 'find_executable', 'chmod', 'execute', 'rmtree',
           'mkdir', 'copy', 'copytree', 'fetch', 'cwd', 'symlink', 'remove',
           'move', 'find', 'textfile', 'env', 'path', 'recipe', 'unpack',
           'patch', 'configure', 'make', 'require_header', 'touch']
