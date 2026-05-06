"""Build the Radia Python extension.

The historical build expected a Unix ``libradia.a`` in ``cpp/gcc``.  This
setup script keeps that mode for existing cluster workflows and adds a Windows
friendly source build so ``python -m pip install .`` can be run from ``cpp/py``
with the Visual Studio Build Tools.
"""

from pathlib import Path
from setuptools import Extension, setup
import os
import platform
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
CPP_DIR = ROOT_DIR / "cpp"
SRC_DIR = CPP_DIR / "src"
EXT_LIB_DIR = ROOT_DIR / "ext_lib"
GLUT_VIEWER_DIR = SRC_DIR / "ext" / "glut_viewer"

CORE_SOURCES = [
    "radapl1.cpp",
    "radapl2.cpp",
    "radapl3.cpp",
    "radapl4.cpp",
    "radapl5.cpp",
    "radapl6.cpp",
    "radapl7.cpp",
    "radarccu.cpp",
    "radcast.cpp",
    "radexpgn.cpp",
    "radflm.cpp",
    "radg3d.cpp",
    "radg3dgr.cpp",
    "radgroup.cpp",
    "radinter.cpp",
    "radintrc.cpp",
    "radiobuf.cpp",
    "radmamet.cpp",
    "radmater.cpp",
    "radplnr1.cpp",
    "radplnr2.cpp",
    "radptrj.cpp",
    "radrec.cpp",
    "radrlmet.cpp",
    "radsbdac.cpp",
    "radsbdep.cpp",
    "radsbdrc.cpp",
    "radsbdvp.cpp",
    "radsend.cpp",
    "radvlpgn.cpp",
]


def env_flag(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in {"", "0", "false", "no", "off"}


def path_list_from_env(name):
    value = os.environ.get(name, "")
    return [str(Path(item).resolve()) for item in value.split(os.pathsep) if item]


def common_include_dirs():
    return [
        SRC_DIR / "lib",
        SRC_DIR / "ext" / "auxparse",
        SRC_DIR / "core",
        SRC_DIR / "ext" / "genmath",
        SRC_DIR / "ext" / "triangle",
    ]


def common_macros():
    return [
        ("MAJOR_VERSION", "1"),
        ("MINOR_VERSION", "0"),
        ("FFTW_ENABLE_FLOAT", None),
        ("NO_TIMER", None),
        ("ANSI_DECLARATORS", None),
        ("TRILIBRARY", None),
        ("_GM_WITHOUT_BASE", None),
        ("ALPHA__LIB__", None),
    ]


GLUT_VIEWER_SOURCES = [
    "glutview.cpp",
    "viewer3d.cpp",
    "simplegraph.cpp",
    "plot2d.cpp",
    "viewerr.cpp",
]

GLUT_VIEWER_EXTRA_SOURCES = [
    SRC_DIR / "ext" / "genmath" / "gmmeth.cpp",
]


def source_files(with_glut: bool = False):
    sources = [
        SRC_DIR / "clients" / "python" / "radpy.cpp",
        SRC_DIR / "lib" / "radentry.cpp",
        SRC_DIR / "ext" / "auxparse" / "auxparse.cpp",
        SRC_DIR / "ext" / "genmath" / "gmfft.cpp",
        SRC_DIR / "ext" / "genmath" / "gmtrans.cpp",
        SRC_DIR / "ext" / "triangle" / "triangle.c",
        *[SRC_DIR / "core" / name for name in CORE_SOURCES],
    ]
    if with_glut:
        sources.extend([GLUT_VIEWER_DIR / name for name in GLUT_VIEWER_SOURCES])
        sources.extend(GLUT_VIEWER_EXTRA_SOURCES)
    return sources


def windows_fftw_library():
    machine = platform.machine().lower()
    return (
        "fftw64_f"
        if "64" in machine or machine in {"amd64", "x86_64"}
        else "fftw_f"
    )


def build_from_source_extension():
    is_windows = os.name == "nt"
    include_dirs = [str(path) for path in common_include_dirs()]
    library_dirs = [str(EXT_LIB_DIR), *path_list_from_env("RADIA_LIBRARY_DIRS")]
    libraries = [windows_fftw_library()] if is_windows else []
    extra_objects = []
    define_macros = common_macros()
    extra_compile_args = []

    if is_windows:
        define_macros.extend([
            ("WIN32", None),
            ("_WINDOWS", None),
            ("_CRT_SECURE_NO_WARNINGS", None),
            ("_CRT_SECURE_NO_DEPRECATE", None),
        ])
        extra_compile_args.extend(["/EHsc"])
        # OpenGL / GLUT 3D viewer support
        conda_prefix = Path(sys.prefix)
        glut_inc = conda_prefix / "Library" / "include"
        glut_lib = conda_prefix / "Library" / "lib"
        if (glut_inc / "GL" / "glut.h").exists():
            define_macros.append(("_WITH_GLUT", None))
            define_macros.append(("Z_BEST_COMPRESSION", "9"))  # from zlib.h, not always available
            include_dirs.append(str(GLUT_VIEWER_DIR))
            include_dirs.append(str(glut_inc))
            library_dirs.append(str(glut_lib))
            libraries.extend(["glut", "opengl32", "glu32", "libpng16", "comdlg32"])
    else:
        define_macros.extend([("__GCC__", None), ("LINUX", None)])
        fftw_archive = EXT_LIB_DIR / (
            "libfftw_f_x86_64.a"
            if platform.machine().lower() in {"amd64", "x86_64"}
            else "libfftw_f_i686.a"
        )
        if fftw_archive.exists() and not env_flag("RADIA_USE_SYSTEM_FFTW"):
            extra_objects.append(str(fftw_archive))
        else:
            libraries.append("fftw3f")
        libraries.extend(["m"])
        extra_compile_args.extend(["-O3", "-Wno-c++11-narrowing"])

    with_glut = ("_WITH_GLUT", None) in define_macros
    return Extension(
        "radia",
        define_macros=define_macros,
        include_dirs=include_dirs,
        libraries=libraries,
        library_dirs=library_dirs,
        sources=[str(path) for path in source_files(with_glut=with_glut)],
        language="c++",
        extra_compile_args=extra_compile_args,
        extra_objects=extra_objects,
    )


def prebuilt_library_extension():
    ext_kwargs = {
        "define_macros": [("MAJOR_VERSION", "1"), ("MINOR_VERSION", "0")],
        "include_dirs": [str(path) for path in common_include_dirs()[:3]],
        "libraries": ["radia", "m", "fftw"],
        "library_dirs": [
            str((CPP_DIR / "gcc").resolve()),
            str(EXT_LIB_DIR.resolve()),
        ],
        "sources": [str((SRC_DIR / "clients" / "python" / "radpy.cpp").resolve())],
        "language": "c++",
    }

    if "MODE" in os.environ:
        sMode = str(os.environ["MODE"])
        if sMode == "mpi":
            ext_kwargs.update({
                "include_dirs": [
                    str(SRC_DIR / "lib"),
                    str(SRC_DIR / "ext" / "auxparse"),
                    str(SRC_DIR / "core"),
                    "/usr/lib/openmpi/include",
                    os.path.abspath(os.environ["MPI_INCLUDE"]),
                ],
                "libraries": ["radia", "m", "fftw", "mpicxx", "dl"],
                "library_dirs": [
                    str((CPP_DIR / "gcc").resolve()),
                    str(EXT_LIB_DIR.resolve()),
                    "/usr/lib/openmpi/lib",
                    os.path.abspath(os.environ["MPI_LIB"]),
                ],
            })
        elif sMode == "mpi_nersc":
            ext_kwargs.update({
                "libraries": ["radia", "m", "fftw", "mpichcxx_intel", "dl"],
                "library_dirs": [
                    str((CPP_DIR / "gcc").resolve()),
                    str(EXT_LIB_DIR.resolve()),
                    os.path.abspath(os.getenv("MPICH_DIR") + "/lib"),
                ],
            })
        elif sMode == "0":
            pass
        else:
            raise Exception("Unknown Radia compilation/linking option")

    return Extension("radia", **ext_kwargs)


# Windows cannot use the Unix libradia.a workflow.  On Unix keep the historical
# default unless explicitly asked to do the self-contained source build.
radia = (
    build_from_source_extension()
    if os.name == "nt" or env_flag("RADIA_BUILD_FROM_SOURCE")
    else prebuilt_library_extension()
)

setup(
    name="radia",
    version="1.0",
    description="This is Radia for Python",
    author="O. Chubar, P. Elleaume, J. Chavanne",
    author_email="chubar@bnl.gov",
    url="http://github.com/ochubar/Radia",
    long_description="This is Python interface to the Radia 3D magnetostatic code.",
    ext_modules=[radia],
)
