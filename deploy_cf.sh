aws s3 cp cloudformation.yaml s3://pat-f-data/strava/cloudformation.yaml

aws cloudformation update-stack --template-url https://pat-f-data.s3.amazonaws.com/strava/cloudformation.yaml --stack-name strava-2021 --region us-east-1 --capabilities CAPABILITY_NAMED_IAM