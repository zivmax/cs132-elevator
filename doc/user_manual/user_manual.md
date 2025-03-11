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
  - [Environment Setup](#environment-setup)
  - [Running the Code](#running-the-code)


---

## Environment Setup

- **Python:** Version 3.10 or higher.
- **Dependencies:** Install the required dependencies using pip:
  - `pip install -r requirements.txt`


## Running the Code

Follow these steps to run the simulation and tests:

**Start the Test Server:**

  - Open a terminal.
  - Navigate to the `/test/` directory.
  - Run: `python main.py`

**Start Your Elevator System:**

  - Open a _separate_ terminal.
  - Navigate to the `/src/` directory.
  - Run: `python main.py`

**Run the Test Case:**
  - In the terminal where you ran `/test/main.py`, you should see a prompt.
  - Type `y` and press Enter to start the naive test case.