import subprocess

def run_build():
    """Compile ESP-IDF project using idf.py build"""
    cmd = ["bash", "-lc", "idf.py set-target ${ESP_IDF_TARGET:-esp32} && idf.py build"]
    p = subprocess.run(cmd, cwd="/workspace", capture_output=True, text=True)
    return (p.stdout or "") + (p.stderr or "")
