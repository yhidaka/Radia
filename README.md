# Radia

3D Magnetostatics Computer Code

## Building on cluster

```sh
make clean
MODE=mpi make all
```

### Python on Linux / clusters

The historical Linux workflow builds the Radia static library first and then
links the Python extension against it:

```sh
cd cpp/gcc
make all
cd ../py
MODE=mpi python setup.py install --user
```

For a self-contained extension build that compiles the Radia C/C++ sources from
`setup.py`, set `RADIA_BUILD_FROM_SOURCE=1`:

```sh
cd cpp/py
RADIA_BUILD_FROM_SOURCE=1 python setup.py build_ext --inplace
```

### Python on Windows

The Python package can now be built directly from `cpp/py` on Windows without
using the legacy Visual Studio solution files.

Requirements:

* 64-bit Python 3 matching the target architecture.
* Microsoft C++ Build Tools / Visual Studio with the MSVC compiler for that
  Python version.
* The checked-in FFTW import libraries in `ext_lib` (`fftw64_f.lib` for 64-bit
  Python or `fftw_f.lib` for 32-bit Python).

Build and install from a "Developer Command Prompt for VS":

```bat
cd cpp\py
py -m pip install .
```

For an in-place development build:

```bat
cd cpp\py
py setup.py build_ext --inplace
py -c "import radia; print(radia.UtiVer())"
```

If FFTW libraries are stored outside the repository, add their folder to
`RADIA_LIBRARY_DIRS` before building; use `;` as the separator on Windows.

### MathLink (Mathematica)

```sh
cd cpp/gcc
make -f Makefile_intermed
```

# Notes

Edit `cpp/gcc/Makefile` files to change Mathematica versions, etc.
