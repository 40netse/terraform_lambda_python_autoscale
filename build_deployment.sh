#!/usr/bin/env bash -vx
cd autoscale
zappa status dev
if [ $? -eq 0 ]
then
    zappa undeploy dev -y --remove-logs --quiet
fi
zappa deploy dev --quiet
url=`zappa status dev |grep "API Gateway URL"|cut -f2-3 -d ":"|sed -e 's/^[ \t]*//'`
cd ..
sed -e "s?API_GATEWAY_URL?$url/sns?g" terraform.tfvars.temp > terraform.tfvars
terraform apply -auto-approve



