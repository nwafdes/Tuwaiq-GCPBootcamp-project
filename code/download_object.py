from google.cloud import storage
import os

def download_file(bucket_name: str, source_blob: str, dest_filename: str) -> str:
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(source_blob)
        if ('/' in dest_filename):
            dest_filename = dest_filename.split('/')[-1]

        dest_path = os.path.join("/tmp", dest_filename)
        blob.download_to_filename(dest_path)


        return {"dest_path":dest_path, "message": f"File {dest_filename} is downloaded successfully"}
    except Exception as e:
        return f"Error downloading file: {e}"