# Deploy a SaaS App to multiple Docker VMs with Docker Swarm

### Step 1: Create VMs and install Docker, create a Swarm and set up a Registry
1. Create 2 or more VMs in Hetzner, DigitalOcean, etc

2. Install Docker on each VM by following the official [Docker Engine Installation guide](https://docs.docker.com/engine/install/#server)

3. [Create a swarm](https://docs.docker.com/engine/swarm/swarm-tutorial/create-swarm/)

4. [Add nodes to the swarm](https://docs.docker.com/engine/swarm/swarm-tutorial/add-nodes/)

5. [Set up a Docker registry](https://docs.docker.com/engine/swarm/stack-deploy/#set-up-a-docker-registry) to store your application images


### Step 2: Verify the status of the swarm

```sh
# View nodes, execute from manager node
docker node ls

# Inspect an individual node
docker node inspect self --pretty
docker node inspect NODE_ID
```


### Step 3: Build and push application images

```sh
# Switch to the microservices-demo directory
cd docker-swarm/microservices-demo
  
# Add the swarm docker registry(127.0.0.1:5000) to the image names in the compose file
cat docker-compose.yml
...
  microservices-demo-api:
    build:
    ...
    image: 127.0.0.1:5000/microservices-demo-api
    container_name: microservices-demo-api
    ...

# Build and push the images
docker compose build
docker compose push

# List the images
docker images
```

### Step 4: Deploy the stack to the swarm
```sh
docker stack deploy --compose-file docker-compose.yml microservices-demo

# Check that it's running 
docker stack services microservices-demo
docker ps # check for containers on all nodes
```

### Step 5: Create a Docker Compose override file. We can add docker stack specific configuration in a docker-compose.override.yml
Increase the replica count of a service. Docker stack configuration can be configured under the deploy section. Learn more about the [Compose Deploy Specification](https://docs.docker.com/reference/compose-file/deploy/)
```sh
cat docker-compose.override.yml

services:

  microservices-demo-api:
    ...
    deploy:
      mode: replicated
      replicas: 3

# Update the stack
docker stack deploy -c docker-compose.yml -c docker-compose.override.yml microservices-demo

# Verify
docker stack services microservices-demo
docker ps # check for replicas on all nodes
```
Add a restart policy
```sh
cat docker-compose.override.yml

services:

  microservices-demo-api:
    ...
    deploy:
      ...
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s

# Update the stack
docker stack deploy -c docker-compose.yml -c docker-compose.override.yml microservices-demo
```

Add resource reservations and limits
```sh
cat docker-compose.override.yml

services:

  microservices-demo-api:
    ...
    deploy:
      ...
      resources:
        limits:
          cpus: '0.50'
          memory: 500M
          pids: 1
        reservations:
          cpus: '0.25'
          memory: 20M

# Update the stack
docker stack deploy -c docker-compose.yml -c docker-compose.override.yml microservices-demo
```

Add placement constraints
```sh
# Add a label to nodes that should only be used for database containers
docker node update --label-add database=true node-1

cat docker-compose.override.yml

services:

  microservices-demo-api:
    ...
    deploy:
      ...
      placement:
        constraints:
          - node.labels.database != true # Prevents the api container from scheduling on a database node
          
# Update the stack
docker stack deploy -c docker-compose.yml -c docker-compose.override.yml microservices-demo
```

Create and mount a config 
```sh
cat docker-compose.override.yml

services:

  microservices-demo-api:
    ...
    deploy:
    ...
    configs:
      - source: settings
        target: /.env
...
configs:
  settings:
    file: ./.env

# Update the stack
docker stack deploy -c docker-compose.yml -c docker-compose.override.yml microservices-demo

# Confirm mounted file
docker exec -it 07d4a2f348a7 cat /.env
```

Create and mount an nfs volume. You need to deploy an nfs server and add all required exports i.e. "/mnt/api" 
```sh
cat docker-compose.override.yml

services:

  microservices-demo-api:
    ...
    deploy:
    ...

    volumes:
      - api-data:/data
...
volumes:
  api-data:
    driver: local
    driver_opts:
      type: "nfs"
      o: "addr=172.20.0.22,rw,sync"
      device: ":/mnt/api"

# Update the stack
docker stack deploy -c docker-compose.yml -c docker-compose.override.yml microservices-demo

# Confirm mounted volume
docker exec -it 07d4a2f348a7 df -h
```

### Step 6: Test External Connectivity
With Docker's built-in routing mesh, you can access any node in the swarm on your application's port and get routed to the app.
```sh
curl http://172.20.0.21:8001/
```
You can create a load balancer with the swarm's VMs as targets and then a service for each exposed service port.