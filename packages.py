"""Packages downloaded by toolchain-m68k.py."""

from collections import namedtuple

# Single source of truth for downloaded packages. The version is written once
# per row; both the download list and the {key} template variables consumed by
# setvar() are derived from this table. The name/url/archive fields are format
# strings that may reference {version} (and {name}); archive defaults to the URL
# basename. sha256, when given, is checked after download.
Package = namedtuple(
    "Package", "key version name url archive sha256", defaults=[None, None]
)

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
        "flex",
        "2.5.4",
        "flex-{version}",
        "https://ftp.gnu.org/old-gnu/gnu-0.2/src/{name}.tar.gz",
    ),
    # Aminet serves the latest NDK 3.2 release as "NDK3.2.lha"; we store it under
    # {name} and pin its checksum, so a new upstream release fails loudly.
    Package(
        "NDK",
        "3.2R4",
        "NDK{version}",
        "https://aminet.net/dev/misc/NDK3.2.lha",
        "{name}.lha",
        "96cabd4ad683dced632e147bf86dee0f50dcb1254386216c25c362916a6409bb",
    ),
    Package(
        "vasm", "2_0f", "vasm{version}", "http://phoenix.owl.de/tags/{name}.tar.gz"
    ),
]


def resolve_package(pkg):
    name = pkg.name.format(version=pkg.version)
    url = pkg.url.format(version=pkg.version, name=name)
    archive = (pkg.archive or url.rsplit("/", 1)[-1]).format(
        version=pkg.version, name=name
    )
    return name, url, archive


PACKAGE_VARS = {pkg.key: resolve_package(pkg)[0] for pkg in PACKAGES}
