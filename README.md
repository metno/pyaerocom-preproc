# PyAerocom PreProcessor

Check observations and model data, and upload them to S3 compatible storage
for later use with PyAerocom on CAMS2_82 and related projects.

## Installation

This command line tool requires Python 3.8 or better.
The recommended installation method is with [`pipx`]:

``` bash
pipx install git+ssh://git@gitlab.met.no/alvarov/pyaerocom-preproc.git
```

File hashes are calculated using the `blake2` algorithm found on Python's standard library, see [`hashlib`].
It is also possible to install with [`blake3`] as an extra dependency for faster file hashes:

``` bash
pipx install pyaerocom-preproc[blake3]@git+ssh://git@gitlab.met.no/alvarov/pyaerocom-preproc.git 
```

[`pipx`]:   https://pypa.github.io/pipx/
[`hashlib`]: https://docs.python.org/3/library/hashlib.html#blake2
[`blake3`]: https://github.com/oconnor663/blake3-py/
