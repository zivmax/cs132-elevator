# User Manual 
- Team-17 Project: Elevator

- Made by LinZheng Tang

---

## Elevator System Simulation and Testing

This document describes how to set up, run, and interact with a simulated elevator system, along with its testing framework. The system uses ZeroMQ (pyzmq) for inter-process communication.

## Content
- [User Manual](#user-manual)
  - [Elevator System Simulation and Testing](#elevator-system-simulation-and-testing)
  - [Content](#content)
  - [1. Environment Setup](#1-environment-setup)
  - [2. Code Structure](#2-code-structure)
  - [3. Running the Code](#3-running-the-code)


---

## 1. Environment Setup

- **Python:** Version 3.10 or higher.
- **Dependencies:** Install the required dependencies using pip:
  - `pip install -r requirements.txt`

## 2. Code Structure

The project is organized into the following directories and files:

- `/src/` - Contains your elevator control logic.

  - `net_client.py`: Handles communication with the testing server (from `/test/`). _You generally don't need to modify this._
  - `main.py`: This is the main file for _your_ elevator control system. Modify this file to implement your logic.

- `/test/` - Contains the testing framework.
  - `main.py`: The main file for the test case runner. This interacts with your system and sends/receives events.
  - `server.py`: Handles communication with your `net_client.py`. _You generally don't need to modify this._

## 3. Running the Code

Follow these steps to run the simulation and tests:

1.  **Start the Test Server:**

    - Open a terminal.
    - Navigate to the `/test/` directory.
    - Run: `python main.py`

2.  **Start Your Elevator System:**

    - Open a _separate_ terminal.
    - Navigate to the `/src/` directory.
    - Run: `python main.py`

3.  **Run the Test Case:**
    - In the terminal where you ran `/test/main.py`, you should see a prompt.
    - Type `y` and press Enter to start the naive test case.