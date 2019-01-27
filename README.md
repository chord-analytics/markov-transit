# Markov Transit Network Reliability Modelling
The purpose of this project is to extend [thesis work](https://prism.ucalgary.ca/handle/1880/106559) done by W. Klumpenhouwer on Markov Chain bus route reliability to a larger transit network.

The project contains the following main components:

* Markov Chain route reliability modelling
* Route transfer modelling and reliability caluclations
* Visualization and mapping of results

These components are outlined in brief below.

## Route Realiability Modelling

## Route Transfer Modelling

## Visualization and Mapping
The visualization and mapping component takes GTFS route, stop, and shape data and combines it with model outputs to generate a shapefile and a dashboard to visualize reliability chokepoints or "hotspots".

## Getting started with Docker
The docker image builds a Ubuntu 18.04 base with Python 3.7 and all the required libraries. It also builds PyBind11 and compiles an optimized version of the truncated lognormal CDF method.

In the example below both the `thesis_data.db` and `CT81.idb` are located inside `markov_transit` directory as they need to be mounted. 
### Launching a shell inside Docker
Step 1: Build the Image
```bash
$ docker build --rm -f "Dockerfile" -t markov-transit:latest .
```
Step 2: Run the container in the background and mount the `markov-transit` directory
```bash
$ docker container run --rm -dit --name markov-transit -v <your-path-here>/markov-transit/:/usr/src/ markov-transit:latest
```
Step 3: To open a shell inside the container:
```
$ docker container exec -it markov-transit bash
```
Once inside the container `python` will be available as a command.

Now try:
```
$ cd /usr/src/; time python get_started.py
```

### Jupyter Notebooks in Docker
Step 1: Same as Step 1 from above.

Step 2: Run the container in the background and mount the `markov-transit` directory and open port 8888.
```bash
$ docker container run --rm -dit --name markov-transit -p 8888:8888 -v <your-path-here>/markov-transit/:/usr/src/ markov-transit:latest
```
Step 3: Run Jupyterlab from the docker container:
```
$ docker container exec -it markov-transit jupyter lab --no-browser --allow-root --port=8888 --ip=0.0.0.0
```