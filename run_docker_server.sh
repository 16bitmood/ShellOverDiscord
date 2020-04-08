rm server_src/users.csv
cp users.csv server_src/users.csv

docker build -t server_main:dev ./server_src
# Run this only once
# docker volume create server_main_home

# Run docker server
docker run --cpus=1 -p 5000:5000\
        -v server_main_home:/home\
        --hostname server_main\
        server_main:dev