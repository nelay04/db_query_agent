import subprocess

try:
    subprocess.run("python manage.py runserver", shell=True)
except KeyboardInterrupt:
    print(f"\033[91m ❌ KeyboardInterrupt!! Server stopped by user.\033[0m")
except Exception as e:
    print(f"\033[91m ❌ Error occurred: {e}\033[0m")
else:
    print(f"\033[91m ❌ Could not start server.\033[0m")
