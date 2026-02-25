#!/bin/bash

# Script to manually trigger the VEX V5 Hub content updater Lambda function
# Uses the 'rdp' AWS profile.

echo "Triggering manual content update for VEX V5 Hub..."

aws lambda invoke \
    --function-name vex5hub-content-updater \
    --invocation-type Event \
    --cli-binary-format raw-in-base64-out \
    --profile rdp \
    /dev/stdout

echo -e "\nUpdate triggered asynchronously. The data will refresh in the background."
echo "Check AWS CloudWatch Logs for /aws/lambda/vex5hub-content-updater for details."
