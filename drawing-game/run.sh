docker stop $(docker ps -q)
docker rm $(docker ps -a -q)
docker build -t final-project:latest .
docker run -d -p 5000:5000 final-project
