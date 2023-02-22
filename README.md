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


## Quick Tutorial

After installation, you may run `pya-pp --help` in the command line to see the various options and commands. Running `--help` after any of the commands shows additoinal information (e.g., `pya-pp report-obs --help`).

A good first step is to run the `check-s3` command to input your credentials. You will be asked to enter the "bucket_name", "access_key_id", and "secret_access_key" provided to you.

After that, you may check the requirements for observation datasets by using `check-obs`. Example syntax for this looks like:

```bash
pya-pp check-obs mep-rd /path/to/data/*.nc
```
 Note the netCDF files in the target directory must follow the naming convention.

 The `report-obs` command follows the same syntax. It checks the files and genreates a report detialing which files do not pass the checks and why. The checksum of files which do not pass are stored in a database. Using the `--clear-cache` option with this command will clear the database, and may be useful if running the command a second time after correcting issues previously found in files.  

The `upload-obs` command will upload files which have previous checks to the servers at MET Norway. It is strongly recommended that this is run only after all checks have passed to ensure all your data is uploaded.
 
