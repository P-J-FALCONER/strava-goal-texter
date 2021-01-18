pip install -r requirements.txt --target ./package --quiet
cd package
zip -q -r ${OLDPWD}/function.zip .
# add function code to zip
cd ../
zip -g function.zip strava.py

aws lambda update-function-code --function-name strava-goal-function --zip-file fileb://function.zip
rm function.zip
rm -rf package/