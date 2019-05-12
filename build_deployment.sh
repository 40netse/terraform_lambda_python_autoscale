#!/usr/bin/env bash -vx
cd modules/iam_lambda
terraform init
terraform apply -auto-approve
cd ../..
cd autoscale
zappa status dev
if [ $? -eq 0 ]
then
    zappa undeploy dev -y --remove-logs --quiet
fi
zappa deploy dev --quiet
url=`zappa status dev |grep "API Gateway URL"|cut -f2-3 -d ":"|sed -e 's/^[ \t]*//'`
cd ..
cat terraform.tfvars |grep -v api_gateway_url > terraform.tfvars.temp
echo "api_gateway_url            = \"API_GATEWAY_URL\"" >> terraform.tfvars.temp
sed -e "s?API_GATEWAY_URL?$url/sns?g" terraform.tfvars.temp > terraform.tfvars
rm -f terraform.tfvars.temp
terraform init
terraform apply -auto-approve



