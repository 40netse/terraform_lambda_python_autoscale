#!/usr/bin/env bash -vx
rm ../build/functions.zip
cd site-packages
zip -r -9 ../../build/functions.zip .
cd ..
zip -g ../build/functions.zip lambda_handler.py
ls -la ../build/functions.zip
cd ../build
aws lambda update-function-code --function-name handler --zip-file fileb://functions.zip
cd ../python


