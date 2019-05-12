#!/usr/bin/env bash -vx
terraform destroy -auto-approve
cd autoscale
zappa undeploy -y --remove-logs
cd ../modules/iam_lambda
terraform destroy -auto-approve
cd ../..
aws dynamodb delete-table --table-name asg-mdw-stage-fgt-autoscale
aws dynamodb delete-table --table-name fortinet_autoscale_us-east-1_730386877786
aws ec2 describe-network-interfaces --output json --filters "Name=status,Values=available"
for eni in `aws ec2 describe-network-interfaces --filters "Name=status,Values=available" --query NetworkInterfaces[*].NetworkInterfaceId`
do
    echo $eni
    aws ec2 delete-network-interface --network-interface-id $eni
done
aws ec2 describe-network-interfaces --output json --filters "Name=status,Values=available"



