import subprocess


subprocess.run(['pyinstaller', '--onedir', 'measure.py', '--clean'])
