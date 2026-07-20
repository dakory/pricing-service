#!/bin/bash
set -euxo pipefail

exec > >(tee /var/log/user-data.log | logger -t user-data -s 2>/dev/console) 2>&1

dnf update -y
dnf install -y docker awscli

systemctl enable docker
systemctl start docker

usermod -aG docker ec2-user

mkdir -p /opt/${app_name}

aws ecr get-login-password --region ${aws_region} \
  | docker login --username AWS --password-stdin ${repository_url}

docker pull ${repository_url}:${image_tag}

docker rm -f ${app_name} || true

docker run -d \
  --name ${app_name} \
  --restart unless-stopped \
  -p ${host_port}:${container_port} \
  ${repository_url}:${image_tag}

echo "Bootstrap finished successfully" > /opt/${app_name}/bootstrap.txt
