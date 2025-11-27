git add .

git commit -m "feat: primer commit"

git push

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 441925558343.dkr.ecr.us-east-1.amazonaws.com

docker build -t pascal-bot .

docker tag pascal-bot:latest 441925558343.dkr.ecr.us-east-1.amazonaws.com/pascal-bot:latest

docker push 441925558343.dkr.ecr.us-east-1.amazonaws.com/pascal-bot:latest