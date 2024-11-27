# Fetch_DE-take-home-bala
Fetch DE Take home assignment 

## How to Run the project

## Setup
Clone this Repo 

```
unzip Fetch-take-home-bala.zip
```
Before running the commands, make sure you have `pip` installed. If not, you can install it by following the instructions on [pip's official documentation](https://pip.pypa.io/en/stable/installation/).



## Installation

### 1. Install Poetry

```bash

pip3 install poetry
or 
python3 -m pip install poetry

```

### 2. Install Dependencies
```
poetry install
```

### 3. Run TestCases
```
poetry run python3 -m coverage run -m unittest discover
poetry run  python3 -m coverage report -m 

```
### 4. Execution (starts Docker compose and Kafka Consumer)
```
make kafka-consumer

```


This command will start the execution of the kafka_consumer, which logs messages sent to processed-user-events topic created withing the code .
please refer Docs for more details about kafka_consumer.py



