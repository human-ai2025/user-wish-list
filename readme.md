# User wishlist app - UPDATE THIS 

Deployed on AWS Elastic Beanstalk using redis and postgreSQL container 

Never commit the enviourment file for servers in production. 

> Github travis integretion 
- Add the docker and aws password in the env variable section of your travis ci repo.
- Keep the same app and env in aws and .travis.yml file 
-  Create a S3 bucket, give it a name, keep the same name in travis file.
- So where there is a change in the main branch, the build is taken, image  pushed to the docker hub and deployed in elstic beanstalk. 

> dockerrun.aws.json
- To manage the images in aws elastic beanstalk we need a similar compose file which aws can understand, so we create dockerrun.aws.json file. Docker compose is for local and dockerrun.aws.json is for AWS. Validate the json files for syntax before deploying it.  

