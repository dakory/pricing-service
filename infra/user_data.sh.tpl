#!/bin/bash
set -euxo pipefail
exec > >(tee /var/log/user-data.log | logger -t user-data -s 2>/dev/console) 2>&1

dnf update -y
dnf install -y docker awscli git
systemctl enable --now docker
usermod -aG docker ec2-user

# Amazon Linux does not currently package the Docker Compose CLI plugin.
mkdir -p /usr/local/lib/docker/cli-plugins
curl -fsSL \
  https://github.com/docker/compose/releases/download/v2.39.1/docker-compose-linux-x86_64 \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod 755 /usr/local/lib/docker/cli-plugins/docker-compose

# A 3 GiB swap file keeps short browser/build peaks from killing PostgreSQL.
if [ ! -f /swapfile ]; then
  dd if=/dev/zero of=/swapfile bs=1M count=3072
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

DEVICE=/dev/nvme1n1
until [ -b "$DEVICE" ]; do sleep 2; done
if ! blkid "$DEVICE"; then mkfs -t xfs "$DEVICE"; fi
mkdir -p /opt/${app_name}
mount "$DEVICE" /opt/${app_name}
grep -q "$DEVICE" /etc/fstab || echo "$DEVICE /opt/${app_name} xfs defaults,nofail 0 2" >> /etc/fstab

aws ecr get-login-password --region ${aws_region} |
  docker login --username AWS --password-stdin ${repository_url}

cat > /opt/${app_name}/deployment.env <<EOF
DOMAIN=${domain}
BACKUP_BUCKET=${backup_bucket}
BACKUP_KMS_KEY_ID=${backup_kms_key}
EOF
chmod 600 /opt/${app_name}/deployment.env

echo "Bootstrap complete. Copy compose sources to /opt/${app_name}, populate .env from SSM, then run docker compose up -d." \
  > /opt/${app_name}/bootstrap.txt
