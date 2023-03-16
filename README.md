# PyAerocom PreProcessor

Check observations and model data, and upload them to S3 compatible storage
for later use with PyAerocom on CAMS2_82 and related projects.

## Installation

This command line tool requires Python 3.8 or better.
The recommended installation method is with [`pipx`]:

``` bash
pipx install git+ssh://git@github.com:metno/pyaerocom-preproc.git
```

File hashes are calculated using the `blake2` algorithm found on Python's standard library, see [`hashlib`].
It is also possible to install with [`blake3`] as an extra dependency for faster file hashes:

``` bash
pipx install pyaerocom-preproc[blake3]@git+ssh://git@gitlab.met.no/alvarov/pyaerocom-preproc.git 
```

[`pipx`]:   https://pypa.github.io/pipx/
[`hashlib`]: https://docs.python.org/3/library/hashlib.html#blake2
[`blake3`]: https://github.com/oconnor663/blake3-py/

## Quick Tutorial

After installation, you may run `pya-pp --help` in the command line to see the various options and commands. Running `--help` after any of the commands shows additional information (e.g., `pya-pp report-obs --help`).

A good first step is to run the `check-s3` command to input your credentials. You will be asked to enter the "bucket_name", "access_key_id", and "secret_access_key" provided to you.

After that, you may check the requirements for observation datasets by using `report-obs`. Example syntax for this looks like:

``` bash
pya-pp report-obs mep-rd /path/to/data/*.nc
```

Note the netCDF files in the target directory must follow the naming convention.

The `report-obs` command checks the files and generates a report detailing which files do not pass the checks and why. While generating the report, the error messages are collected and stored on a database. This way files with known errors do not need to be re-tested.
The `--clear-cache` option will clear the database, allowing the files to be re-checked from scratch.

The `upload-obs` command will upload files which have previous checks to the servers at MET Norway. It is strongly recommended that this is run only after all checks have passed to ensure all your data is uploaded.
