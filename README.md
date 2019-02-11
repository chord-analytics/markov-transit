# Markov Transit Network Reliability Modelling
The purpose of this project is to extend [thesis work](https://prism.ucalgary.ca/handle/1880/106559) done by W. Klumpenhouwer on Markov Chain bus route reliability to a larger transit network.

The project contains the following main components:

* Markov Chain route reliability modelling
* Route transfer modelling and reliability caluclations
* Visualization and mapping of results

These components are outlined in brief below.

## Route Reliability Modelling

## Route Transfer Modelling
Route transfer modelling focuses on collections of stops that are considered 'transfer points' for the network. For now, we will focus on the following three transfer points as a proof of concept:
* University - Craigie Hall
* Chinook LRT Station
* Mount Royal University

### Transfer Data
The script ```utility/build_transfers_json.py``` (still under construction) will gather the necessary information for transfer points in a given 'hub' and print it to a json file currently named ```transfers.json```. This file can be read into a python dictionary, and so calls can be made to each attribute heirarchically:
* ``network`` - a network name such as 'Calgary Transit'.
* ``details`` - details about the data or network in question
* ``hubs`` - a list of hub objects with the following properties
    * ``name`` - display name for the individual hub
    * ``transfer_time`` - time in minutes required to transfer buses at the hub
    * ``hub_lat`` - the latitude of the hub location for display purposes
    * ``hub_lon`` - the longitude of the hub location for display purposes.
    * ``transfer_rate`` - the fraction of passengers who use the stop that are transferring.
    * ``stops`` - a list of stops with the following properties:
        * ``stop_id`` - the id of the stop
        * ``stop_name`` - the name of the stop
        * ``stop_code`` - lookup code for GTFS/website
        * ``stop_lat`` - latitude of stop location
        * ``stop_lon`` - longitude of stop location
    * ``routes`` - a list of routes with the following properites:
        * ``route_id`` - the id of the route
        * ``stop_seq`` - the sequence of the route's stop at the hub
        * ``nb`` - the average boardings for a bus on the route at the hub stop
        * ``na`` - the average alightings for a bus on the route at the hub stop
        * ``theta`` - the average through passengers for a bus on the route at the hub stop
        * ``route_number``  - the route's display number
        * ``route_name`` - the name of the route (and the scheduled attached)
        * ``daily_count`` - the daily number of buses that run on the route
    * ``transfers`` - transfer counts between routes
        * ``from_id`` - the route from which transfers are happening
        * ``to_id`` - the route to which transfers are occuring
        * ``daily_transfer`` the number of people who transfer on each route.

This transfer data can be used to build route models and calculate total missed transfers at a given hub.

#### Determining Transfer Flows
In order to determine the number of passengers transferring to each stop, we will need to make some assumptions from the data:
* The number of passengers who "transfer" at a given hub is a fixed fraction of the total number of alighting passengers.
* The distribution of the of passengers who "transfer" at a given stop is given by the boarding pattern at that stop. For example, if a certain route has 10% of all boardings, it will get 10% of transfers.

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