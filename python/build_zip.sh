#!/usr/bin/env bash
rm ../build/functions.zip
cd site-packages
zip -r -9 ../../functions.zip
cd ..
zip -g ../functions.zip lambda_handler.py
ls -la ../functions.zip
