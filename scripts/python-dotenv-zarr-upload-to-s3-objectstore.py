import os
import sys

import s3fs
import xarray
import zarr
from dotenv import load_dotenv

# By default load_dotenv will look for the .env file in the current working directory or any parent directories
load_dotenv()

access_key = os.getenv("S3_BUCKET_ACCESS_KEY")
secret_key = os.getenv("S3_BUCKET_SECRET_KEY")

if len(sys.argv) != 2:
    raise ValueError("Provide path to netCDF file")

print(f"Using file {sys.argv[1]}")

inputnetcdf = sys.argv[1]

ds = xarray.open_dataset(inputnetcdf)

# AWS S3 path
s3_path = "s3://cams282-user5/zarr_data"

# Initilize the S3 file system
s3 = s3fs.S3FileSystem(
    key=access_key, secret=secret_key, client_kwargs={"endpoint_url": "https://rgw.met.no"}
)

store = s3fs.S3Map(root=s3_path, s3=s3, check=False)

# Compare the data if needed
compressor = zarr.Blosc(cname="zstd", clevel=3)
encoding = {vname: {"compressor": compressor} for vname in ds.data_vars}

# Save to zarr
ds.to_zarr(store=store, encoding=encoding, consolidated=True)
