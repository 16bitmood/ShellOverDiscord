# Shell Over Discord
An experimental discord bot interface to a shell running inside docker. Kind of like SSH.

## Running the bot
- Place your DISCORD_TOKEN at discord_bot/.env
- `./run_discord_bot.sh`

## Running the server
- Place the unique discord user_id and nickname inside users.csv file for as many users as you want(see example.users.csv). user_id must be unique discord user_id. But, nickname can be anything.
- scripts and binaries placed in server_src/shared will be available to all users.
- `./run_docker_server.sh`
