import os
import shutil
import uuid
import abc
from typing import Optional
import mimetypes

class StorageService(abc.ABC):
    @abc.abstractmethod
    def save(self, file_obj, filename: str) -> str:
        """Save file and return the path/identifier"""
        pass

    @abc.abstractmethod
    def delete(self, filename: str):
        """Delete file"""
        pass

    @abc.abstractmethod
    def get_url(self, filename: str) -> str:
        """Get public URL for the file"""
        pass

class LocalStorage(StorageService):
    def __init__(self, upload_dir: str = "uploads", base_url: str = "/uploads"):
        self.upload_dir = upload_dir
        self.base_url = base_url
        os.makedirs(self.upload_dir, exist_ok=True)

    def save(self, file_obj, filename: str) -> str:
        # Generate unique filename to prevent collisions if not already unique
        # But caller might persist filename. 
        # Strategy: Caller ensures uniqueness or we do.
        # Social router does: f"{uuid.uuid4()}_{file.filename}"
        # So we just take filename.
        filepath = os.path.join(self.upload_dir, filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)
        return filename

    def delete(self, filename: str):
        filepath = os.path.join(self.upload_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)

    def get_url(self, filename: str) -> str:
        # If filename is a path like "uploads/foo.jpg", strip uploads/
        # But currently code stores "uploads/filename" in DB?
        # Let's check social.py: 
        # filepath = os.path.join("uploads", filename)
        # photo = Photo(..., photo_path=filepath)
        # So DB has "uploads/uuid_foo.jpg"
        
        # We need to handle this. Ideally StorageService manages the "uploads/" prefix if local.
        # If migration happens, old paths have "uploads/".
        
        # For new storage abstraction:
        # save() should return what is stored in DB.
        # If we use OCI, we typically store just the object name or key.
        # If we use Local, we stored "uploads/filename".
        
        # To support existing DB: 
        # If using LocalStorage, we probably stick to "uploads/filename" as the key.
        
        if filename.startswith(self.upload_dir + "/"):
            return f"/{filename}" # Relative URL mounted at /uploads/filename -> /uploads/filename works if /uploads is mounted
            # Wait, app.mount("/uploads"...)
            # URL is /uploads/filename.
            # Filename in DB is "uploads/filename".
            # So returning "/" + filename works.
        return f"{self.base_url}/{filename}"

class OCIStorage(StorageService):
    def __init__(self):
        import oci
        self.config = {
            "user": os.environ.get("OCI_USER"),
            "fingerprint": os.environ.get("OCI_FINGERPRINT"),
            "key_file": os.environ.get("OCI_KEY_FILE"),
            "tenancy": os.environ.get("OCI_TENANCY"),
            "region": os.environ.get("OCI_REGION")
        }
        # Validate config if needed, or rely on OCI SDK validation
        self.client = oci.object_storage.ObjectStorageClient(self.config)
        self.namespace = os.environ.get("OCI_NAMESPACE")
        if not self.namespace:
             self.namespace = self.client.get_namespace().data
        self.bucket_name = os.environ.get("OCI_BUCKET_NAME")

    def save(self, file_obj, filename: str) -> str:
        # Strip "uploads/" if present for OCI object name cleanliness, or keep it?
        # To match local structure, we might want to keep uniqueness.
        # But "uploads/" folder notion in Object Storage is just prefix.
        
        # Let's clean the filename for OCI but store the resulting ID/Key in DB.
        # Social router expects save to return something that is stored in DB.
        
        # If we want to switch seamlessly, we should probably stick to a convention.
        # Let's just use the filename passed to us.
        
        # Read file content
        content = file_obj.read()
        # Reset file pointer if needed, or assume it's fresh. 
        # SpooledTemporaryFile might need seek(0).
        if hasattr(file_obj, 'seek'):
            file_obj.seek(0)
            content = file_obj.read()
            
        self.client.put_object(
            self.namespace,
            self.bucket_name,
            filename,
            content,
            content_type=mimetypes.guess_type(filename)[0]
        )
        return filename

    def delete(self, filename: str):
        try:
            self.client.delete_object(self.namespace, self.bucket_name, filename)
        except Exception as e:
            print(f"Error deleting object {filename}: {e}")

    def get_url(self, filename: str) -> str:
        # Public URL format: https://objectstorage.{region}.oraclecloud.com/n/{namespace}/b/{bucket}/o/{object}
        # We need to handle / encoding if filename has slashes.
        # OCI SDK might have a helper or we construct it.
        region = self.config["region"]
        return f"https://objectstorage.{region}.oraclecloud.com/n/{self.namespace}/b/{self.bucket_name}/o/{filename}"

def get_storage_service() -> StorageService:
    storage_type = os.getenv("STORAGE_TYPE", "local").lower()
    if storage_type == "oci":
        return OCIStorage()
    return LocalStorage()
