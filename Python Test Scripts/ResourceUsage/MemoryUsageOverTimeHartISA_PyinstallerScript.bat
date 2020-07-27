pip.exe install pyinstaller
pip.exe install -r requirements.txt
pyinstaller.exe MemoryUsageOverTimeHartISA.py --clean --onefile --path "./../ISA 100 Testing Scripts/ISADeviceCount" --path "./../Gateway Web Scraping Tools/GwDeviceCount"
