# Fairyring CLI
Fairyring CLI is a Python command-line tool for monitoring events on the Fairyring blockchain and sending alerts to Slack.

## Features
* Monitor aggregated key events (subscribe_aggregated_key)
* Monitor transfer events for a specific address and minimum amount (subscribe_transfer)
* Monitor execution of encrypted transactions (subscribe_encrypted_tx)

## Dependencies
* Python 3.10+
* websockets
* requests
* python-dotenv

## Installation
Clone the repository:
```bash
git clone https://github.com/magu007/fairyring-cli.git
```
Install dependencies:
```bash
pip install websockets requests python-dotenv
```
Set environment variable
```bash
cp .env.example .env
```
and add your own Slack webhook url in `.env`:


## Usage
```bash
python fairyring_cli.py <command> [args]
```
### Commands
* subscribe_aggregated_key: Monitor aggregated key events
* subscribe_transfer [address] [amount]: Monitor transfer events for a specific address and minimum amount
* subscribe_encrypted_tx [tx_hash]: Monitor execution of a specific encrypted transaction

## Docker
You can also run this tool using Docker.

Build the Docker image:
```bash
docker build -t fairyring-cli .
```

Run the Docker container:
```bash
docker run --env-file .env fairyring-cli <command> [args]
```
