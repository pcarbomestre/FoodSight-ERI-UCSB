This Lambda function's simplicity enables direct deployment from a zip file. 
The zip file should include both the Lambda function itself and its dependencies. 
The dependencies can be installed using the following command:

pip install requests boto3 -t .