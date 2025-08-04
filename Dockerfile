FROM python:3.11-slim

# Install PowerShell 7 for Linux so we can use Test-Connection -TcpPort -Quiet
RUN apt-get update && apt-get install -y wget apt-transport-https software-properties-common gnupg &&     wget -q https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb &&     dpkg -i packages-microsoft-prod.deb &&     apt-get update && apt-get install -y powershell &&     rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy your bot code
COPY . .

# Default command. Update if your entrypoint filename differs.
CMD ["python", "main_linux_only.py"]
