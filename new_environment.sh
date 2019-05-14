#!/bin/bash
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install awscli -y
sudo apt-get install python3.7 python3.7-pip python3.7-venv -y
python3.7 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip3.7 install -r requirements.txt
sudo snap install terraform

tput clear
echo
echo "Provide AWS Credentials via "aws configure" and deployment specific parameters"
echo
echo
aws configure
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
# Ask the user for an s3 bucket name that doesn't exist
#
echo -n "Provide a unique S3 Bucket for the deployment to use: "
read userInput
if [[ -n "$userInput" ]]
then
    s3_bucket=$userInput
fi

#
# Ask the user for a keypair that exists in the region
#
echo -n "Provide a region specific keypair ec2 instances to use: "
read userInput
if [[ -n "$userInput" ]]
then
    keypair=$userInput
fi
tput clear

#
# Now modify the approriate files based on user input
#
# replace everything between the two quotes on the line that starts with aws_region with the region user input
# then build the availability zones using the region... its assumed that it will be 1a and 1b
#
sed -i '/^aws_region/ s/"[^"][^"]*"/"'$region'"/' terraform.tfvars
sed -i '/^availability_zone1/ s/"[^"][^"]*"/"'$region'a"/' terraform.tfvars
sed -i '/^availability_zone2/ s/"[^"][^"]*"/"'$region'b"/' terraform.tfvars
#
# replace everything between the second set of two quotes on the line that contains with "aws_region":
# with the region user input for the autoscale/zappa_settings.json file
#
sed -i '/"aws_region":/ s/"[^"][^"]*"/"'$region'"/2' autoscale/zappa_settings.json
#
# replace everything between the second set of two quotes on the line that contains with "s3_bucket":
# with the s3_bucket user input for the autoscale/zappa_settings.json file
#
sed -i '/"s3_bucket":/ s/"[^"][^"]*"/"'$s3_bucket'"/2' autoscale/zappa_settings.json
#
# replace everything between the set of two quotes on the line that contains with "keypair":
# with the keypair user input for the terraform.tfvars file
#
sed -i '/^keypair/ s/"[^"][^"]*"/"'$keypair'"/' terraform.tfvars

tput clear
echo "Verify the terraform.tfvars and autoscale/zappa_settings.json file for correct parameters"
tput clear