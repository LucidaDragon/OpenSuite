# OpenSuite
An open source, decentralized, and modular replacement for cloud services, including Accounts, Drive, E-Mail, Calendar, and more.

## Quick Start
1. OpenSuite requires Python 3.10+ to run. You can download it [here](https://www.python.org/downloads/).
2. Start the server with the following command: ```python main.py```
3. Open a web browser and connect to the server by navigating to [http://localhost:8080/](http://localhost:8080/).

## Configuration
### Server Port & Allowed Addresses
By default the server is hosted on port 8080 and allows connections from all addresses (0.0.0.0). This can be changed in ```./config.py```.
### Persistent Storage Providers
By default SQLite is used to store persistent data. To supplement a module's data storage provider with a different one, create a Python script defining the appropriate API for that module and import it as the provider in ```./modules/<module_name>/config.py```.