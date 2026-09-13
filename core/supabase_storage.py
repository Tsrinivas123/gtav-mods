import os
import mimetypes
import json
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def get_supabase_url():
    url = getattr(settings, 'SUPABASE_URL', '') or os.getenv('SUPABASE_URL', '')
    return url.rstrip('/')


def get_supabase_service_key():
    return getattr(settings, 'SUPABASE_SERVICE_KEY', '') or os.getenv('SUPABASE_SERVICE_KEY', '') or os.getenv('SUPABASE_KEY', '')


def get_supabase_bucket():
    return getattr(settings, 'SUPABASE_BUCKET', '') or os.getenv('SUPABASE_BUCKET', 'pawanmod-files')


def is_configured():
    """Returns True if valid Supabase URL and Service Key are present."""
    url = get_supabase_url()
    key = get_supabase_service_key()
    return bool(url and key and url.startswith(('http://', 'https://')))


def get_headers(content_type=None, upsert=True):
    key = get_supabase_service_key()
    headers = {
        'Authorization': f'Bearer {key}',
        'apikey': key,
    }
    if content_type:
        headers['Content-Type'] = content_type
    if upsert:
        headers['x-upsert'] = 'true'
    return headers


def upload_file(file_data, remote_path, content_type=None):
    """
    Uploads bytes or file-like object to private Supabase Storage bucket.
    """
    if not is_configured():
        raise RuntimeError("Supabase Storage is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY.")

    url = get_supabase_url()
    bucket = get_supabase_bucket()
    remote_path = remote_path.lstrip('/')

    if not content_type:
        guessed, _ = mimetypes.guess_type(remote_path)
        content_type = guessed or 'application/octet-stream'

    endpoint = f"{url}/storage/v1/object/{bucket}/{remote_path}"
    headers = get_headers(content_type=content_type, upsert=True)

    if hasattr(file_data, 'read'):
        if hasattr(file_data, 'seek'):
            file_data.seek(0)
        data = file_data.read()
    else:
        data = file_data

    response = requests.post(endpoint, data=data, headers=headers, timeout=30)
    if response.status_code in (200, 201):
        return {
            'status': 'success',
            'path': remote_path,
            'response': response.json() if response.text else {}
        }
    else:
        error_msg = f"Supabase upload failed [{response.status_code}]: {response.text}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def delete_file(remote_path):
    """
    Deletes a single file from the private Supabase Storage bucket.
    """
    if not is_configured():
        return False

    url = get_supabase_url()
    bucket = get_supabase_bucket()
    remote_path = remote_path.lstrip('/')

    # Never delete shared placeholder images
    if 'placeholder' in remote_path.lower():
        return True

    endpoint = f"{url}/storage/v1/object/{bucket}"
    headers = get_headers(content_type='application/json')
    payload = json.dumps({"prefixes": [remote_path]})

    try:
        response = requests.delete(endpoint, data=payload, headers=headers, timeout=15)
        return response.status_code in (200, 204)
    except Exception as e:
        logger.warning(f"Error deleting {remote_path} from Supabase: {e}")
        return False


def create_signed_url(remote_path, expires_in=300):
    """
    Creates a time-limited signed URL for private bucket objects (e.g. secure mod downloads).
    expires_in: lifetime in seconds (default 300 seconds = 5 minutes).
    """
    if not is_configured():
        return None

    url = get_supabase_url()
    bucket = get_supabase_bucket()
    remote_path = remote_path.lstrip('/')

    endpoint = f"{url}/storage/v1/object/sign/{bucket}/{remote_path}"
    headers = get_headers(content_type='application/json')
    payload = json.dumps({"expiresIn": int(expires_in)})

    try:
        response = requests.post(endpoint, data=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            signed_path = data.get('signedURL', '')
            if not signed_path:
                return None
            if signed_path.startswith('http://') or signed_path.startswith('https://'):
                return signed_path
            if signed_path.startswith('/storage/v1'):
                return f"{url}{signed_path}"
            elif signed_path.startswith('/'):
                return f"{url}/storage/v1{signed_path}"
            else:
                return f"{url}/storage/v1/{signed_path}"
        else:
            logger.warning(f"Failed to generate signed URL for {remote_path}: {response.status_code} {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception generating signed URL for {remote_path}: {e}")
        return None


def download_file_bytes(remote_path):
    """
    Downloads raw file bytes from private Supabase Storage bucket using Service Key.
    """
    if not is_configured():
        return None

    url = get_supabase_url()
    bucket = get_supabase_bucket()
    remote_path = remote_path.lstrip('/')

    endpoint = f"{url}/storage/v1/object/authenticated/{bucket}/{remote_path}"
    headers = get_headers()

    try:
        response = requests.get(endpoint, headers=headers, stream=True, timeout=30)
        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
        logger.error(f"Exception downloading {remote_path} from Supabase: {e}")
        return None


def file_exists(remote_path):
    """
    Checks if a file exists in the Supabase Storage bucket.
    """
    if not is_configured():
        return False

    url = get_supabase_url()
    bucket = get_supabase_bucket()
    remote_path = remote_path.lstrip('/')

    # Check directory and filename via list API
    folder = os.path.dirname(remote_path)
    filename = os.path.basename(remote_path)

    endpoint = f"{url}/storage/v1/object/list/{bucket}"
    headers = get_headers(content_type='application/json')
    payload = json.dumps({
        "prefix": folder,
        "search": filename,
        "limit": 10
    })

    try:
        response = requests.post(endpoint, data=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            items = response.json()
            return any(item.get('name') == filename for item in items if isinstance(item, dict))
        return False
    except Exception:
        return False
