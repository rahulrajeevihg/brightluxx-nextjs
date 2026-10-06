"""
CDN Upload Helper - Uploads files to external CDN server via SFTP.
Auto-optimizes images (resize, compress, WebP conversion) before upload.
"""
import paramiko
import os

# External CDN configuration (env-driven; defaults point at the live file server)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass
CDN_HOST = os.getenv("CDN_HOST", "152.42.185.192")
CDN_USER = os.getenv("CDN_USER", "root")
CDN_PASS = os.getenv("CDN_PASS", "")
CDN_BASE_PATH = os.getenv("CDN_BASE_PATH", "/var/brightluxx")
CDN_BASE_URL = os.getenv("CDN_BASE_URL", "https://files.ihgbrands.com/brightluxx")


def _ensure_remote_dir(sftp, full_path: str):
    """Ensure remote directory exists, creating recursively if needed."""
    try:
        sftp.stat(full_path)
    except FileNotFoundError:
        parts = full_path.split('/')
        current = ''
        for part in parts:
            if part:
                current += f'/{part}'
                try:
                    sftp.stat(current)
                except FileNotFoundError:
                    sftp.mkdir(current)


def _sftp_upload(filename: str, content: bytes, subfolder: str) -> str:
    """Raw SFTP upload — no image processing."""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(CDN_HOST, username=CDN_USER, password=CDN_PASS, timeout=30)

        sftp = ssh.open_sftp()
        full_path = f"{CDN_BASE_PATH}/{subfolder}"
        _ensure_remote_dir(sftp, full_path)

        remote_path = f"{full_path}/{filename}"
        with sftp.file(remote_path, 'wb') as f:
            f.write(content)
        sftp.chmod(remote_path, 0o644)

        sftp.close()
        ssh.close()
        return f"{CDN_BASE_URL}/{subfolder}/{filename}"
    except Exception as e:
        print(f"CDN upload error: {e}")
        raise Exception(f"Failed to upload to CDN: {str(e)}")


def upload_to_cdn(filename: str, content: bytes, subfolder: str = "uploads") -> str:
    """Upload file to CDN (no optimization)."""
    return _sftp_upload(filename, content, subfolder)


def upload_image_to_cdn(filename: str, content: bytes, category: str = "uploads") -> str:
    """Upload an image to the CDN with auto-optimization (WebP + resize + compress)."""
    from image_optimizer import optimize_image, get_image_info

    original_info = get_image_info(content)
    original_size = len(content)

    optimized_content, new_ext = optimize_image(content)
    optimized_size = len(optimized_content)

    # Update filename extension if converted
    if new_ext:
        base = os.path.splitext(filename)[0]
        filename = f"{base}{new_ext}"
        content_to_upload = optimized_content
    else:
        content_to_upload = content

    saved_pct = round((1 - optimized_size / original_size) * 100, 1) if original_size > 0 else 0
    print(f"Image optimization: {original_info.get('width', '?')}x{original_info.get('height', '?')} "
          f"{original_info.get('format', '?')} {original_size:,}B -> {optimized_size:,}B "
          f"({saved_pct}% saved) -> {filename}")

    return _sftp_upload(filename, content_to_upload, category)


def upload_video_to_cdn(filename: str, content: bytes) -> str:
    """Upload a video to the CDN."""
    return _sftp_upload(filename, content, "videos")


def upload_document_to_cdn(filename: str, content: bytes) -> str:
    """Upload a document (PDF, etc.) to the CDN."""
    return _sftp_upload(filename, content, "resources")
