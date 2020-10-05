pip.exe install pyinstaller
pip.exe install -r requirements.txt
pyinstaller.exe "./GUI/MemoryTracker.py" --clean --onefile --path "./../ISA 100 Testing Scripts/ISADeviceCount" --path "./../Gateway Web Scraping Tools/GwDeviceCount" --path "./../SSHHelper"
