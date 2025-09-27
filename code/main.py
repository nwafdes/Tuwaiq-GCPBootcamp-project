import base64, json, logging, functions_framework, os
# from download_file import download_gcs_object
import json
from google.cloud import storage
from read_file import extract_content
from download_object import download_file
from cloudevents.http import CloudEvent

logging.basicConfig(level=logging.INFO)

@functions_framework.cloud_event
def handle_pubsub_cloudevent(event) -> None:
    logging.info(f"event: {event}")
    # this will make the event a python dict
    data = event.data or {}
    msg = data.get('message', {})
    if not msg:
        logging.warning("msg is not set; skipping")
        return  # acknowledges the event; no retry
    encrypted_data = msg.get('data','')

    if not encrypted_data:
        logging.warning("data is not set; skipping")
        return
    
    data = base64.b64decode(encrypted_data)
    data = json.loads(data)

    bucket = data.get("bucket","")
    object_id = data.get("name","")
    content_type = data.get("contentType","")

    cloud_storage_downloaded_file = download_file(bucket, object_id, object_id)

    content = extract_content(cloud_storage_downloaded_file['dest_path'])
    
    logging.info(f"File content: {content}")
    # return content