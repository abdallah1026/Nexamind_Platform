import argparse
import requests
import os
import sys

def upload_document(tenant_id, file_path, host="http://localhost:8003"):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)
        
    url = f"{host}/api/v1/documents/upload"
    headers = {
        "X-Tenant-Id": tenant_id
    }
    
    filename = os.path.basename(file_path)
    print(f"Uploading {filename} to {url} for tenant {tenant_id}...")
    
    with open(file_path, "rb") as f:
        files = {
            "file": (filename, f, "text/plain")
        }
        data = {
            "collection": "default"
        }
        
        try:
            resp = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            resp.raise_for_status()
            print("Upload successful!")
            print(resp.json())
        except Exception as e:
            print(f"Upload failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(e.response.text)
            sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload document to NexaMind RAG service")
    parser.add_argument("--tenant-id", required=True, help="Tenant UUID")
    parser.add_argument("--file", default="scripts/tesla_operational_policy.txt", help="Path to file to upload")
    parser.add_argument("--host", default="http://localhost:8003", help="RAG service host url")
    args = parser.parse_args()
    
    upload_document(args.tenant_id, args.file, args.host)
