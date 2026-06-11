#!/usr/bin/env python3

# Build cross toolchain for AmigaOS <= 3.9 / M68k target.

from collections import namedtuple
from fnmatch import fnmatch
from glob import glob
from logging import info, getLogger
from os import environ
import argparse
import logging
import platform
import sys

# Single source of truth for downloaded packages. The version is written once
# per row; both the download list and the {key} template variables consumed by
# setvar() are derived from this table. The name/url/archive fields are format
# strings that may reference {version} (and {name}); archive defaults to the URL
# basename. Rows with key=None are downloaded but not exposed as a variable.
Package = namedtuple("Package", "key version name url archive", defaults=[None])

PACKAGES = [
    Package("m4", "1.4.17", "m4-{version}", "https://ftp.gnu.org/gnu/m4/{name}.tar.gz"),
    Package(
        "gawk", "3.1.8", "gawk-{version}", "https://ftp.gnu.org/gnu/gawk/{name}.tar.gz"
    ),
    Package(
        "autoconf",
        "2.13",
        "autoconf-{version}",
        "https://ftp.gnu.org/gnu/autoconf/{name}.tar.gz",
    ),
    Package(
        "bison",
        "1.35",
        "bison-{version}",
        "https://ftp.gnu.org/gnu/bison/{name}.tar.gz",
    ),
    Package(
        "texinfo",
        "4.12",
        "texinfo-{version}",
        "https://ftp.gnu.org/gnu/texinfo/{name}.tar.gz",
    ),
    Package(
        "automake",
        "1.15",
        "automake-{version}",
        "https://ftp.gnu.org/gnu/automake/{name}.tar.gz",
    ),
    Package(
        "gmp",
        "6.2.1",
        "gmp-{version}",
        "https://gcc.gnu.org/pub/gcc/infrastructure/{name}.tar.bz2",
    ),
    Package(
        "mpfr",
        "3.1.6",
        "mpfr-{version}",
        "https://gcc.gnu.org/pub/gcc/infrastructure/{name}.tar.bz2",
    ),
    Package(
        "mpc",
        "1.0.3",
        "mpc-{version}",
        "https://gcc.gnu.org/pub/gcc/infrastructure/{name}.tar.gz",
    ),
    Package(
        "isl",
        "0.18",
        "isl-{version}",
        "https://gcc.gnu.org/pub/gcc/infrastructure/{name}.tar.bz2",
    ),
    Package(
        "shrinkler",
        "4.7",
        "Shrinkler-{version}",
        "https://github.com/askeksa/Shrinkler/archive/refs/tags/v{version}.tar.gz",
        "{name}.tar.gz",
    ),
    Package(
        "salvador",
        "1.4.2",
        "salvador-{version}",
        "https://github.com/emmanuel-marty/salvador/archive/refs/tags/{version}.tar.gz",
        "{name}.tar.gz",
    ),
    Package(
        "lzsa",
        "1.4.1",
        "lzsa-{version}",
        "https://github.com/emmanuel-marty/lzsa/archive/refs/tags/{version}.tar.gz",
        "{name}.tar.gz",
    ),
    Package(
        "sdl",
        "3.4.10",
        "SDL-{version}",
        "https://github.com/libsdl-org/SDL/archive/refs/tags/release-{version}.tar.gz",
        "{name}.tar.gz",
    ),
    Package(
        "sdl_image",
        "3.4.4",
        "SDL_image-{version}",
        "https://github.com/libsdl-org/SDL_image/archive/refs/tags/release-{version}.tar.gz",
        "{name}.tar.gz",
    ),
    Package(
        "flex",
        "2.5.4",
        "flex-{version}",
        "https://ftp.gnu.org/old-gnu/gnu-0.2/src/{name}.tar.gz",
    ),
    # alinea-computer serves the NDK as "NDK39.lha"; we store it under {name}.
    Package(
        "NDK",
        "3.9",
        "NDK_{version}",
        "http://hp.alinea-computer.de/AmigaOS/NDK39.lha",
        "{name}.lha",
    ),
    Package(
        None,
        "1_9c",
        "vasm",
        "http://phoenix.owl.de/tags/vasm{version}.tar.gz",
        "vasm.tar.gz",
    ),
]


def resolve_package(pkg):
    name = pkg.name.format(version=pkg.version)
    url = pkg.url.format(version=pkg.version, name=name)
    archive = (pkg.archive or url.rsplit("/", 1)[-1]).format(
        version=pkg.version, name=name
    )
    return name, url, archive


PACKAGE_VARS = {pkg.key: resolve_package(pkg)[0] for pkg in PACKAGES if pkg.key}


from common import (  # noqa: E402
    setvar,
    execute,
    rmtree,
    remove,
    configure,
    unpack,
    path,
    panic,
    mkdir,
    env,
    make,
    touch,
    patch,
    require_header,
    require_packages,
    copy,
    cwd,
    recipe,
    find_executable,
    textfile,
    chmod,
    copytree,
    move,
    find,
    fetch,
    exists,
    join,
)


@recipe("target-prepare")
def prepare_target():
    info("preparing target")

    with cwd("{prefix}"):
        mkdir("bin", "etc", "{target}")
    with cwd("{prefix}/{target}"):
        mkdir(
            "bin",
            "ndk/include/inline",
            "ndk/include/lvo",
            "ndk/lib",
            "ndk/lib/fd",
            "ndk/lib/sfd",
        )


@recipe("vasm-install")
def install_vasm():
    info("installing vasm")

    copy("{build}/vasm/vasmm68k_mot", "{prefix}/{target}/bin")
    vasm = textfile(
        "#!/bin/sh",
        "",
        '{prefix}/{target}/bin/vasmm68k_mot -I{prefix}/{target}/ndk/include "$@"',
    )
    chmod(vasm, 0o755)
    move(vasm, "{prefix}/bin/vasm")


@recipe("{NDK}-install")
def install_ndk():
    info("installing ndk")

    copytree("{sources}/{NDK}/Include/include_h", "{prefix}/{target}/ndk/include")
    copytree("{sources}/{NDK}/Include/include_i", "{prefix}/{target}/ndk/include")
    copytree("{sources}/{NDK}/Include/fd", "{prefix}/{target}/ndk/lib/fd")
    copytree("{sources}/{NDK}/Include/sfd", "{prefix}/{target}/ndk/lib/sfd")
    copytree(
        "{sources}/{NDK}/Include/linker_libs",
        "{prefix}/{target}/ndk/lib",
        exclude=["README"],
    )
    copytree("{sources}/{NDK}/Documentation/Autodocs", "{prefix}/{target}/ndk/doc")

    for name in find("{prefix}/{target}/ndk/lib/sfd", include=["*.sfd"]):
        base = path.basename(name).split("_")[0]

        execute(
            "sfdc",
            "--target=m68k-amigaos",
            "--mode=proto",
            "--output={prefix}/{target}/ndk/include/proto/%s.h" % base,
            name,
        )
        execute(
            "sfdc",
            "--target=m68k-amigaos",
            "--mode=macros",
            "--output={prefix}/{target}/ndk/include/inline/%s.h" % base,
            name,
        )
        execute(
            "sfdc",
            "--target=m68k-amigaos",
            "--mode=lvo",
            "--output={prefix}/{target}/ndk/include/lvo/%s_lib.i" % base,
            name,
        )


@recipe("fd2sfd-install")
def install_fd2sfd():
    info("installing fd2sfd")

    copy("{build}/fd2sfd/fd2sfd", "{prefix}/bin")
    copy(
        "{build}/fd2sfd/cross/share/{target}/alib.h",
        "{prefix}/{target}/ndk/include/inline",
    )


@recipe("fd2pragma-install")
def install_fd2pragma():
    info("installing fd2pragma")

    copy("{build}/fd2pragma/fd2pragma", "{prefix}/bin")
    for header in ["macros.h", "stubs.h"]:
        copy(
            join("{build}/fd2pragma/Include/inline", header),
            "{prefix}/{target}/ndk/include/inline",
        )


@recipe("shrinkler-install")
def install_shrinkler():
    info("installing shrinkler")

    copy("{build}/{shrinkler}/build/native/Shrinkler", "{prefix}/bin/Shrinkler")


@recipe("salvador-install")
def install_salvador():
    info("installing salvador")

    copy("{build}/{salvador}/salvador", "{prefix}/bin/salvador")


@recipe("lzsa-install")
def install_lzsa():
    info("installing lzsa")

    copy("{build}/{lzsa}/lzsa", "{prefix}/bin/lzsa")


@recipe("fs-uae-bootstrap")
def fs_uae_bootstrap():
    info("bootstrapping fs-uae")

    with cwd("{submodules}/{fsuae}"):
        execute("sh", "bootstrap")


@recipe("cmake", 1)
def cmake_configure(name, *opts, src_dir=None):
    info('configuring "%s" with cmake', name)

    src = src_dir or join("{submodules}", name)
    with cwd(join("{build}", name)):
        execute("cmake", "-S", src, "-B", ".", "-G", "Unix Makefiles", *opts)


def update_autotools(dst):
    copy("{sources}/{automake}/lib/config.guess", join(dst, "config.guess"))
    copy("{sources}/{automake}/lib/config.sub", join(dst, "config.sub"))


def touch_genfiles(dst):
    """
    For binutils and gcc we want to make sure C source & headers file doesn't get
    regenerated. Otherwise it can cause weird errors later in the build process
    (e.g. in ldexp.c:560)
    """
    for name in find(dst, include=["*.l", "*.y"]):
        basename = path.splitext(name)[0]
        for c_file in glob(basename + ".c"):
            touch(c_file)
        for h_file in glob(basename + ".h"):
            touch(h_file)


def download():
    with cwd("{archives}"):
        for pkg in PACKAGES:
            _, url, archive = resolve_package(pkg)
            fetch(archive, url)

    execute("git", "submodule", "init")
    execute("git", "submodule", "update")


def prepare_build_env():
    for var in list(environ.keys()):
        if var not in ["_", "LOGNAME", "HOME", "SHELL", "TMPDIR", "PWD"]:
            del environ[var]

    PATHS = ["/usr/bin", "/bin"]

    """
  Make sure we always choose known compiler (from the distro) and not one in
  user's path that could shadow the original one.
  """
    if platform.system() == "Darwin":
        CC, CXX = "clang", "clang++"
        PATHS.append("/usr/local/bin")
        PATHS.append("/usr/local/opt/gettext/bin")
    else:
        CC, CXX = "gcc", "g++"

    if fnmatch(platform.system(), "MSYS_NT*"):
        PATHS.append("/usr/bin/core_perl")  # pod2text, pod2man

    PATH = ":".join(PATHS)

    environ["PATH"] = PATH
    environ["LANG"] = "C"
    environ["TERM"] = "xterm"

    CC = find_executable(CC)
    CXX = find_executable(CXX)
    FLAGS = "-s -O2 -pipe"

    if getLogger().isEnabledFor(logging.DEBUG):
        FLAGS += " -Wall"
    else:
        FLAGS += " -w"
        environ["MAKEFLAGS"] = "--silent"

    environ["CC"] = CC
    environ["CXX"] = CXX
    environ["PATH"] = ":".join([join("{prefix}", "bin"), join("{host}", "bin"), PATH])

    setvar(cc=environ["CC"], cxx=environ["CXX"], flags=FLAGS, path=PATH)

    """
  When we have a working compiler in our path, we shoule also check if the
  required programs, headers and libraries are present.
  """

    find_executable("perl")
    find_executable("pod2text")
    find_executable("pod2man")
    find_executable("gperf")
    find_executable("patch")
    find_executable("make")
    find_executable("makeinfo")
    find_executable("git")
    find_executable("yacc")
    find_executable("cmake")

    require_header(
        ["ncurses.h", "ncurses/ncurses.h"],
        lang="c",
        errmsg="libncurses-dev package missing",
    )

    """
  On Debian-based systems check upfront that every development package the build
  relies on is installed, so a missing library fails fast with an apt-get hint
  instead of a cryptic error deep inside the SDL/amiberry build. This list is the
  source of truth mirrored by the Dockerfile.
  """
    require_packages(
        "libsdl2-dev",
        "libsdl2-ttf-dev",
        "libpng-dev",
        "libncurses-dev",
        "libglib2.0-dev",
        "libopenal-dev",
        # SDL3 video/audio/input backends
        "libx11-dev",
        "libxext-dev",
        "libxcursor-dev",
        "libxi-dev",
        "libxfixes-dev",
        "libxrandr-dev",
        "libxrender-dev",
        "libxss-dev",
        "libxkbcommon-dev",
        "libwayland-dev",
        "wayland-protocols",
        "libdecor-0-dev",
        "libgl1-mesa-dev",
        "libegl1-mesa-dev",
        "libgles2-mesa-dev",
        "libdrm-dev",
        "libgbm-dev",
        "libasound2-dev",
        "libpulse-dev",
        "libudev-dev",
        "libdbus-1-dev",
        # SDL3_image codecs / AmiBerry deps
        "libjpeg-dev",
        "libflac-dev",
        "libmpg123-dev",
        "libcurl4-openssl-dev",
        "nlohmann-json3-dev",
        "zlib1g-dev",
    )


def phase_download():
    download()
    # Make sure the command does not output an error when you commit the patches
    execute("quilt", "push", "-a", ignore_errors=True)


def phase_host_tools():
    unpack("{automake}")

    unpack("{m4}")
    patch("{m4}")
    configure("{m4}", "--prefix={host}")
    make("{m4}", parallel=True)
    make("{m4}", "install")

    unpack("{gawk}")
    update_autotools("{sources}/{gawk}")
    patch("{gawk}")
    configure("{gawk}", "--prefix={host}")
    make("{gawk}", parallel=True)
    make("{gawk}", "install")

    unpack("{flex}")
    patch("{flex}")
    configure("{flex}", "--prefix={host}")
    make("{flex}")
    make("{flex}", "install")

    unpack("{bison}")
    update_autotools("{sources}/{bison}/config")
    patch("{bison}")
    configure("{bison}", "--prefix={host}")
    make("{bison}", parallel=True)
    make("{bison}", "install")

    unpack("{texinfo}")
    patch("{texinfo}")
    update_autotools("{sources}/{texinfo}/build-aux")
    configure("{texinfo}", "--prefix={host}")
    make("{texinfo}", parallel=True)
    make("{texinfo}", "install")

    unpack("{autoconf}")
    update_autotools("{sources}/{autoconf}")
    configure("{autoconf}", "--prefix={host}")
    make("{autoconf}", parallel=True)
    make("{autoconf}", "install")


def phase_gcc_deps():
    unpack("{gmp}")
    configure("{gmp}", "--prefix={host}", "--disable-shared", "--enable-static")
    make("{gmp}", parallel=True)
    make("{gmp}", "install")

    unpack("{mpfr}")
    configure(
        "{mpfr}",
        "--prefix={host}",
        "--with-gmp={host}",
        "--disable-shared",
        "--enable-static",
    )
    make("{mpfr}", parallel=True)
    make("{mpfr}", "install")

    unpack("{mpc}")
    configure(
        "{mpc}",
        "--prefix={host}",
        "--with-gmp={host}",
        "--with-mpfr={host}",
        "--disable-shared",
        "--enable-static",
    )
    make("{mpc}", parallel=True)
    make("{mpc}", "install")

    unpack("{isl}")
    configure(
        "{isl}",
        "--prefix={host}",
        "--with-gmp-prefix={host}",
        "--disable-shared",
        "--enable-static",
    )
    make("{isl}", parallel=True)
    make("{isl}", "install")


def phase_target():
    prepare_target()

    unpack("vasm", work_dir="{build}")
    make("vasm", CPU="m68k", SYNTAX="mot")
    install_vasm()

    update_autotools("{submodules}/fd2sfd")
    unpack("fd2sfd", work_dir="{build}")
    configure("fd2sfd", "--prefix={prefix}", from_dir="{build}/fd2sfd")
    make("fd2sfd")
    install_fd2sfd()

    unpack("fd2pragma", work_dir="{build}")
    make("fd2pragma")
    install_fd2pragma()

    unpack("sfdc")
    configure("sfdc", "--prefix={prefix}", copy_source=True)
    make("sfdc")
    make("sfdc", "install")

    unpack("{NDK}")
    patch("{NDK}")
    install_ndk()


def phase_binutils():
    with env(
        CC="{cc}", CXX="{cxx}", CFLAGS="{flags}", CXXFLAGS="{flags}", PATH="{path}"
    ):
        configure(
            "{binutils}",
            "--prefix={prefix}",
            "--infodir={prefix}/{target}/info",
            "--mandir={prefix}/share/man",
            "--disable-nls",
            "--disable-plugins",
            "--disable-werror",
            "--disable-tui",
            "--with-libgmp-prefix={host}",
            "--with-python=" + sys.executable,
            "--target=m68k-amigaos",
            from_dir="{submodules}/{binutils}",
        )
        touch_genfiles("{submodules}/{binutils}")
        make("{binutils}", "configure-gdb")
        make("{binutils}", "all-bfd", parallel=True)
        make("{binutils}", "all-binutils", parallel=True)
        make("{binutils}", "all-gas", parallel=True)
        make("{binutils}", "all-ld", parallel=True)
        make("{binutils}", "all-gdb", parallel=True)
        make("{binutils}", "install-binutils")
        make("{binutils}", "install-gas")
        make("{binutils}", "install-ld")
        make("{binutils}", "install-gdb")


def phase_gcc():
    with env(
        CC="{cc} -std=gnu99",
        CXX="{cxx} -std=gnu++11",
        CFLAGS="{flags}",
        CXXFLAGS="{flags}",
    ):
        configure(
            "{gcc}",
            "--prefix={prefix}",
            "--infodir={prefix}/{target}/info",
            "--mandir={prefix}/share/man",
            "--host=i686-linux-gnu",
            "--build=i686-linux-gnu",
            "--target=m68k-amigaos",
            "--enable-languages=c",
            "--enable-version-specific-runtime-libs",
            from_dir="{submodules}/{gcc}",
        )
        touch_genfiles("{submodules}/{gcc}")
        touch("{submodules}/{gcc}/gcc/c-parse.gperf")
        touch("{submodules}/{gcc}/gcc/configure")
        # parallel build fails for all-gcc
        make("{gcc}", "all-gcc", MAKEINFO="makeinfo")
        make("{gcc}", "install-gcc", MAKEINFO="makeinfo")


def phase_gcc_bebbo():
    with env(CC="{cc}", CXX="{cxx}", CFLAGS="{flags}", CXXFLAGS="{flags}"):
        configure(
            "{gcc_bebbo}",
            "--prefix={prefix}",
            "--infodir={prefix}/{target}/info",
            "--mandir={prefix}/share/man",
            "--program-prefix=m68k-amigaos-",
            "--program-suffix=-6.5.0b",
            "--with-gmp={host}",
            "--with-mpfr={host}",
            "--with-mpc={host}",
            "--with-isl={host}",
            "--target=m68k-amigaos",
            "--enable-languages=c",
            "--enable-version-specific-runtime-libs",
            "--disable-nls",
            "--disable-libssp",
            from_dir="{submodules}/{gcc_bebbo}",
        )
        make("{gcc_bebbo}", "all-gcc", parallel=True)
        make("{gcc_bebbo}", "install-gcc")


def phase_fs_uae():
    with env(
        CC="{cc}", CXX="{cxx}", CFLAGS="{flags}", CXXFLAGS="{flags}", PATH="{path}"
    ):
        fs_uae_bootstrap()
        configure(
            "{fsuae}",
            "--prefix={prefix}",
            "--enable-gdbstub",
            "--without-libmpeg2",
            "--disable-action-replay",
            "--disable-ahi",
            "--disable-builtin-slirp",
            "--disable-gfxboard",
            "--disable-jit",
            "--disable-lua",
            "--disable-netplay",
            "--disable-pearpc-cpu",
            "--disable-ppc",
            "--disable-prowizard",
            "--disable-slirp",
            "--disable-qemu-cpu",
            "--disable-qemu-slirp",
            "--disable-uaescsi",
            "--disable-uaeserial",
            "--disable-dms",
            "--disable-zip",
            from_dir="{submodules}/{fsuae}",
        )
        make("{fsuae}", parallel=True)
        make("{fsuae}", "install")


def phase_sdl():
    with env(
        CC="{cc}", CXX="{cxx}", CFLAGS="{flags}", CXXFLAGS="{flags}", PATH="{path}"
    ):
        unpack("{sdl}", top_dir="SDL-release-3.4.10")
        cmake_configure(
            "{sdl}",
            "-DCMAKE_BUILD_TYPE=Release",
            "-DCMAKE_INSTALL_PREFIX={host}",
            "-DSDL_SHARED=ON",
            "-DSDL_STATIC=OFF",
            "-DSDL_TEST_LIBRARY=OFF",
            "-DSDL_X11_XTEST=OFF",
            src_dir="{sources}/{sdl}",
        )
        make("{sdl}", parallel=True)
        make("{sdl}", "install")

        unpack("{sdl_image}", top_dir="SDL_image-release-3.4.4")
        cmake_configure(
            "{sdl_image}",
            "-DCMAKE_BUILD_TYPE=Release",
            "-DCMAKE_INSTALL_PREFIX={host}",
            "-DCMAKE_PREFIX_PATH={host}",
            "-DBUILD_SHARED_LIBS=ON",
            "-DSDLIMAGE_VENDORED=OFF",
            "-DSDLIMAGE_SAMPLES=OFF",
            "-DSDLIMAGE_TESTS=OFF",
            src_dir="{sources}/{sdl_image}",
        )
        make("{sdl_image}", parallel=True)
        make("{sdl_image}", "install")


def phase_amiberry():
    with env(
        CC="{cc}", CXX="{cxx}", CFLAGS="{flags}", CXXFLAGS="{flags}", PATH="{path}"
    ):
        cmake_configure(
            "{amiberry}",
            "-DCMAKE_BUILD_TYPE=Release",
            "-DCMAKE_INSTALL_PREFIX={prefix}",
            "-DCMAKE_PREFIX_PATH={host}",
            "-DBUNDLE_SDL=ON",
            "-DUSE_JIT=OFF",
            "-DUSE_PCEM=OFF",
            "-DUSE_LIBSERIALPORT=OFF",
            "-DUSE_LIBENET=OFF",
            "-DUSE_PORTMIDI=OFF",
            "-DUSE_LIBMPEG2=OFF",
            "-DUSE_UAENET_PCAP=OFF",
            "-DUSE_UAENET_TAP=OFF",
            "-DUSE_ZSTD=OFF",
        )
        make("{amiberry}", parallel=True)
        make("{amiberry}", "install")


def phase_compressors():
    unpack("{shrinkler}", work_dir="{build}")
    make("{shrinkler}")
    install_shrinkler()

    unpack("{salvador}", work_dir="{build}")
    make("{salvador}", CC="gcc")
    install_salvador()

    unpack("{lzsa}", work_dir="{build}")
    make("{lzsa}", CC="gcc")
    install_lzsa()


# Ordered build phases. `build` with no arguments runs them all in order; named
# arguments (e.g. "build amiberry") run only those phases, assuming their
# dependencies were already built. Stamps still gate the steps inside each phase.
BUILD_PHASES = [
    ("download", phase_download),
    ("host-tools", phase_host_tools),
    ("gcc-deps", phase_gcc_deps),
    ("target", phase_target),
    ("binutils", phase_binutils),
    ("gcc", phase_gcc),
    ("gcc-bebbo", phase_gcc_bebbo),
    ("fs-uae", phase_fs_uae),
    ("sdl", phase_sdl),
    ("amiberry", phase_amiberry),
    ("compressors", phase_compressors),
]


def _component_names():
    return [name for name, _ in BUILD_PHASES]


def _validate_components(names):
    available = _component_names()
    unknown = [n for n in names if n not in available]
    if unknown:
        panic(
            "unknown build component(s): %s; available: %s",
            ", ".join(unknown),
            ", ".join(available),
        )
    return available


def build(*names):
    available = _validate_components(names)
    selected = set(names) if names else set(available)
    prepare_build_env()
    for name, fn in BUILD_PHASES:
        if name in selected:
            fn()


def rebuild(*names):
    if not names:
        panic(
            "rebuild requires at least one build component; available: %s",
            ", ".join(_component_names()),
        )
    _validate_components(names)
    for name in names:
        remove(glob(join("{stamps}", f"{name}-make*")))
    build(*names)


def clean():
    rmtree("{stamps}")
    rmtree("{sources}")
    rmtree("{host}")
    rmtree("{build}")
    rmtree("{tmpdir}")
    execute("quilt", "pop", "-a", ignore_errors=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

    if "VIRTUAL_ENV" not in environ:
        panic('Please run "source activate" before executing this script.')

    if not sys.version_info[:2] >= (3, 11):
        panic("I need Python 3.11 to run!")

    if not any(
        fnmatch(platform.system(), pat)
        for pat in ["Darwin", "Linux", "CYGWIN_NT*", "MSYS_NT*"]
    ):
        panic("Build on %s not supported!", platform.system())

    if platform.machine() not in ["i686", "x86_64"]:
        panic("Build on %s architecture not supported!", platform.machine())

    parser = argparse.ArgumentParser(
        description="Build cross toolchain.",
        epilog="build components (in order): " + ", ".join(_component_names()),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "action",
        choices=["build", "clean", "download", "rebuild"],
        default="build",
        help="perform action",
    )
    parser.add_argument(
        "args",
        metavar="ARGS",
        type=str,
        nargs="*",
        help="build components to (re)build (default: all); see list below",
    )
    parser.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument(
        "--prefix", type=str, default=None, help="installation directory"
    )
    args = parser.parse_args()

    setvar(top=path.abspath(path.dirname(sys.argv[0])))

    setvar(
        **PACKAGE_VARS,
        binutils="binutils-gdb",
        fsuae="fs-uae",
        amiberry="amiberry",
        gcc="gcc-2.95.3",
        gcc_bebbo="gcc-bebbo",
        target="m68k-amigaos",
        python=sys.executable,
        patches=join("{top}", "patches"),
        stamps=join("{top}", ".build-m68k", "stamps"),
        build=join("{top}", ".build-m68k", "build"),
        sources=join("{top}", ".build-m68k", "sources"),
        host=join("{top}", ".build-m68k", "host"),
        tmpdir=join("{top}", ".build-m68k", "tmp"),
        prefix=join("{top}", "m68k-amigaos"),
        archives=join("{top}", ".build-m68k", "archives"),
        submodules=join("{top}", "submodules"),
    )

    if args.quiet:
        getLogger().setLevel(logging.INFO)

    if args.prefix is not None:
        setvar(prefix=args.prefix)

    if not exists("{prefix}"):
        mkdir("{prefix}")

    action = args.action.replace("-", "_")
    globals()[action].__call__(*args.args)
