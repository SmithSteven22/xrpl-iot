# IoT-based payment system

## Overview
The IoT-based payment system integrates IoT devices with the XRP Ledger (XRPL) for seamless microtransactions. The system enables smart cards to manage subscription- or time-based services and automates XRP payments based on usage. It aims to create sustainable commerce and resource management solutions, removing intermediaries by leveraging blockchain technology.

## Project Structure
```
xrpl-iot/
|-- database/
|   |-- clients_database.csv       # Database containing user and card details
|-- iotknit/
|   |-- .venv/                     # Python virtual environment
|   |-- middleware.py              # Middleware handling transactions and MQTT communication
|-- nodered/
    |-- system.json                # Node-RED flows for UI and backend integration
```

### Folder Descriptions
1. **database/**
   - Contains the client data in `clients_database.csv`. This file is crucial for mapping card IDs to user details, service types, and account information.

2. **iotknit/**
   - Contains the Python environment and the middleware script `middleware.py`. The middleware interacts with the XRPL, processes smart card events, and publishes results via MQTT.

3. **nodered/**
   - Houses the `system.json` file, which defines the Node-RED flows used to display user data and manage interactions.

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node-RED
- Git

### Installation
1. **Clone the Repository**
   ```bash
   git clone git@github.com:your-username/xrpl-iot.git
   cd xrpl-iot
   ```

2. **Set Up the Python Environment**
   ```bash
   cd iotknit
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .\.venv\Scripts\activate  # Windows
   pip install pandas xrpl-py iotknit
   ```

3. **Configure Node-RED**
   - Import the `system.json` flow into Node-RED.
   - Ensure the MQTT broker is configured to receive and publish messages.

4. **Prepare the Database**
   - Add user and card information to `clients_database.csv`. Ensure the required fields are present (e.g., `user_id`, `card_id`, `service_type`, etc.).

## Usage
1. **Run the Middleware**
   ```bash
   python3 iotknit/middleware.py
   ```

2. **Interact via Node-RED UI**
   - Use the UI to monitor transactions, view user details, and check statuses.

3. **Process Smart Card Events**
   - The middleware listens for card events and handles transactions accordingly.

## Development
### Adding a Feature
- Modify `middleware.py` for logic updates.
- Update Node-RED flows for UI enhancements.

### Testing
- Ensure proper testing with mock data in `clients_database.csv`.
- Validate end-to-end flow: card detection -> middleware processing -> XRPL transaction -> Node-RED display.

## Microtransactions for IoT Systems
IoT systems can enable sustainable commerce and resource management by removing intermediaries through blockchain technology. The XRPL-IoT project explores the integration of XRP Ledger into IoT systems for efficient microtransactions. 

### Potential Applications
- Automatic coffee machines
- Vending machines
- Event payment tokens
- Monetizing interactive art or advanced NFTs
- Scientific publication remuneration systems

The goal is to create an easy-to-use framework for designing, developing, and testing IoT systems that leverage blockchain for payments.

## Contribution
1. Fork the repository.
2. Create a feature branch.
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes and push.
4. Create a pull request.

## License
This project is licensed under the MIT License.

