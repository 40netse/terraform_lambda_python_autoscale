#!/bin/bash -vx
sudo apt-get install awscli -y
aws configure
sudo apt-get install python3 python3-pip python3-venv -y
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip3 install -r requirements.txt
sudo snap install terraform
#
# Ask the user which region to deploy to
#
echo -n "Which aws region would you like to deploy in: "
read userInput
if [[ -n "$userInput" ]]
then
    region=$userInput
fi
#
# replace everything between the two quotes on the line that starts with aws_region with the region user input
#
sed -i '/^aws_region/ s/"[^"][^"]*"/"'$region'"/' terraform.tfvars
#
# replace everything between the second set of two quotes on the line that contains with "aws_region":
# with the region user input
#
sed -i '/"aws_region":/ s/"[^"][^"]*"/"'$region'"/2' autoscale/zappa_settings.json

#
# Ask the user for an s3 bucket name that doesn't exist
#
echo -n "Provide a unique S3 Bucket for the deployment to use: "
read userInput
if [[ -n "$userInput" ]]
then
    s3_bucket=$userInput
fi
sed -i '/"aws_region":/ s/"[^"][^"]*"/"'$s3_bucket'"/2' autoscale/zappa_settings.json

#
# Ask the user for a keypair that exists in the region
#
echo -n "Provide a region specific keypair ec2 instances to use: "
read userInput
if [[ -n "$userInput" ]]
then
    keypair=$userInput
fi
sed -i '/"aws_region":/ s/"[^"][^"]*"/"'$keypair'"/2' autoscale/zappa_settings.json

