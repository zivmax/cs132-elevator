# User Manual

---

## Table of Contents

- [User Manual](#user-manual)
  - [Table of Contents](#table-of-contents)
  - [System Requirements](#system-requirements)
    - [Minimum System Requirements](#minimum-system-requirements)
  - [Installation \& Setup](#installation--setup)
    - [Packaged Version Installation (Recommended)](#packaged-version-installation-recommended)
    - [Source Code Version (For Developers)](#source-code-version-for-developers)
  - [Getting Started](#getting-started)
    - [Launching the Application](#launching-the-application)
    - [Understanding the Initial State](#understanding-the-initial-state)
    - [Quick Start Tutorial](#quick-start-tutorial)
  - [User Interface Overview](#user-interface-overview)
    - [Main Window Layout](#main-window-layout)
    - [Building Visualization Details](#building-visualization-details)
    - [Control Panel Features](#control-panel-features)
    - [Debug Information Panel](#debug-information-panel)
  - [Basic Operations](#basic-operations)
    - [Calling an Elevator](#calling-an-elevator)
    - [Selecting Your Destination](#selecting-your-destination)
    - [Manual Door Control](#manual-door-control)
  - [Command Line Options](#command-line-options)
    - [Basic Command Line Usage](#basic-command-line-usage)
    - [Available Options](#available-options)
    - [Common Command Line Examples](#common-command-line-examples)

---

## System Requirements

### Minimum System Requirements

- Windows with WebView2 Supported
- `uv` installed

## Installation & Setup

### Packaged Version Installation (Recommended)

1. **Download the Application**

   - Locate the `elevator.exe` file provided by your instructor or system administrator
   - Ensure the file is saved to an easily accessible location (e.g., Desktop or Program Files)
2. **Verify File Integrity**

   - Check that the file size matches the expected distribution
   - Scan with antivirus software if required by your organization
3. **No Installation Required**

   - The application is portable and runs directly from the executable file
   - No system modifications or registry changes are made

<!-- Screenshot placeholder: Application executable file in Windows Explorer -->

![alt text](images/explorer_view.png)


### Source Code Version (For Developers)
1. **Clone the Repository**

   - Use Git to clone the repository:
     ```
     git clone <repository_url>
     ```

2. **Install Dependencies**
   - Navigate to the project directory:
     ```
     cd <repository_directory>/system
     ```
   - Install required packages using `uv`:
     ```
     uv sync
     ```

3. **Check Installation**
   - Ensure all dependencies are installed correctly
   - Run the application using:
     ```
     uv run main.py
     ```
     
---

## Getting Started

### Launching the Application

1. **Standard Launch**

   - Double-click `elevator.exe` to start the application
   - Wait for the loading screen to complete (typically 3-5 seconds)
   - The main simulation window will appear automatically
2. **Verifying Successful Launch**

   - Look for the building visualization with two elevator shafts
   - Confirm that floor call buttons are visible on the left side
   - Check that elevator control panels are displayed on the right side

<!-- Screenshot placeholder: Main application window upon startup -->

![alt text](images/app_window.png)

### Understanding the Initial State

When the application starts:

- Both elevators begin at Floor 1 (ground floor)
- All doors are closed
- No active calls or destinations are set
- The system is ready to receive commands

🟢 **Success Indicator**: You should see two elevator cars positioned at Floor 1 with closed doors and no directional arrows lit.

### Quick Start Tutorial

**Follow these steps for your first interaction:**

1. **Call an Elevator**

   - Click the "▲" (up) button next to Floor 2
   - Watch as one elevator begins moving upward
   - Observe the directional arrow indicator
2. **Select a Destination**

   - While the elevator is at Floor 2, click "3" in the elevator's control panel
   - The elevator will move to Floor 3 automatically
3. **Manual Door Control**

   - Click the "◀ ▶" button to open doors manually
   - Click the "▶ ◀" button to close doors

🔵 **Tip**: Doors will automatically close after a few seconds if left open.

---

## User Interface Overview

### Main Window Layout

The application window consists of four main sections arranged for optimal usability:

<!-- Screenshot placeholder: Annotated main window showing all four sections -->

![alt text](images/app_fullview.png)

**A. Building Visualization (Top)**

- Visual representation of the 5-floor building
- Elevator shafts with moving elevator cars
- Floor call buttons for summoning elevators

**B. Elevator Control Panels (Middle)**

- Individual control panels for each elevator
- Destination selection buttons
- Manual door control buttons
- Real-time floor and direction indicators

**C. Status Information (Bottom)**

- Current elevator positions
- Active calls and destinations
- System status messages

**D. Debug Information (Bottom)** *[Optional]*

- Technical details about elevator states
- Target floor queues
- Detailed status information

### Building Visualization Details

**Floor Layout:**

- Floor 3: Top floor, down button only
- Floor 2: Middle floor, up and down buttons
- Floor 1: Ground floor, up and down buttons
- Floor -1: Basement, up button only

**Elevator Cars:**

- Numbered "1" and "2" for identification
- Visual door animation (opening/closing)
- Position updates in real-time
- Color coding for different states

**Call Buttons:**

- **▲ Up Button**: Request elevator going upward
- **▼ Down Button**: Request elevator going downward
- **Active State**: Buttons light up when pressed
- **Reset**: Buttons return to normal when elevator arrives

### Control Panel Features

Each elevator has an identical control panel containing:

**Floor Selection Buttons:**

- Large, numbered buttons for each floor (3, 2, 1, -1)
- Buttons highlight when selected as destinations
- Multiple floors can be selected simultaneously

**Door Control Buttons:**

- **"◀ ▶" Open Doors**: Manually opens elevator doors
- **"▶ ◀" Close Doors**: Manually closes elevator doors
- Immediate response to button presses

**Status Display:**

- **Floor Indicator**: Shows current elevator floor
- **Direction Arrows**: Indicate movement direction (▲ up, ▼ down)
- **Real-time Updates**: Information updates continuously

<!-- Screenshot placeholder: Close-up of elevator control panel with labeled components -->

![alt text](images/user_panel.png)

### Debug Information Panel

🔵 **Note**: Debug information is hidden by default. Enable it using the `--debug` command line option.

The debug panel provides technical details:

- **Current Floor**: Precise floor position
- **Status**: Operating state (IDLE, MOVING_UP, MOVING_DOWN, etc.)
- **Door**: Door state (OPEN, CLOSED, OPENING, CLOSING)
- **Target Floors**: Queue of destination floors

---

## Basic Operations

### Calling an Elevator

**Purpose**: Summon an elevator to your current floor

**Steps:**

1. Identify your current floor on the building visualization
2. Determine your intended direction (up or down)
3. Click the appropriate call button:
   - **▲** for going up to higher floors
   - **▼** for going down to lower floors
4. Wait for the elevator to arrive (button will remain lit)
5. The button will reset when an elevator reaches your floor

**Example Scenario:**

- You're on Floor 2 and want to go to Floor 3
- Click the "▲" button next to Floor 2
- Watch as the nearest available elevator moves to Floor 2
- The elevator doors will open automatically upon arrival

⚠️ **Important**: Always select the correct direction button. Elevators optimize their routes based on the direction of your call.

### Selecting Your Destination

**Purpose**: Choose which floor you want to visit

**Steps:**

1. Ensure you're "inside" an elevator (doors are open at your floor)
2. Look at the control panel for the appropriate elevator
3. Click the button corresponding to your destination floor
4. The button will light up to confirm your selection
5. The elevator will automatically close doors and move to your destination

**Multiple Destinations:**

- You can select multiple floors for one trip
- The elevator will visit floors in optimal order
- Each destination button will light up when selected

**Floor Button Reference:**

- **"3"**: Top floor
- **"2"**: Second floor
- **"1"**: Ground floor (main entrance)
- **"-1"**: Basement level

<!-- Screenshot placeholder: Control panel with destination button highlighted -->

![alt text](images/user_panel_floor_highlighted.png)

### Manual Door Control

**Purpose**: Override automatic door operations

**When to Use:**

- Hold doors open for additional passengers
- Close doors immediately without waiting
- Emergency situations requiring door control

**Open Doors Manually:**

1. Click the "◀ ▶" button in the elevator control panel
2. Doors will open immediately
3. Doors will remain open until manually closed or timeout occurs

**Close Doors Manually:**

1. Click the "▶ ◀" button in the elevator control panel
2. Doors will close immediately
3. If elevator has destinations, movement will begin automatically

🔴 **Safety Note**: Manual door controls only work when the elevator is stopped at a floor. Moving elevators cannot have doors opened.

## Command Line Options

The application supports several command line parameters for advanced users and system administrators.

### Basic Command Line Usage

**Opening Command Prompt:**

1. Press `Windows + R` to open Run dialog
2. Type `cmd` and press Enter
3. Navigate to the application directory using `cd` command
4. Run the application with desired options

**Basic Syntax:**

```
elevator.exe [OPTIONS]
```

### Available Options

**--debug**

- **Purpose**: Enable debug information display
- **Usage**: `elevator.exe --debug`
- **Effect**: Shows technical details in the bottom panel
- **Recommended for**: Troubleshooting, technical demonstrations

**--headless**

- **Purpose**: Run without graphical interface
- **Usage**: `elevator.exe --headless`
- **Effect**: Starts backend services only, no GUI window
- **Use case**: Server deployments, automated testing

**--ws-port [PORT]**

- **Purpose**: Specify WebSocket communication port
- **Usage**: `elevator.exe --ws-port 18675`
- **Default**: Automatically finds available port (18675-18775 range)
- **Use case**: Avoiding port conflicts, network restrictions

**--http-port [PORT]**

- **Purpose**: Specify HTTP server port
- **Usage**: `elevator.exe --http-port 19090`
- **Default**: Automatically finds available port (19090-19190 range)
- **Use case**: Custom web server configuration

**--zmq-port [PORT]**

- **Purpose**: Set ZMQ communication port for external systems
- **Usage**: `elevator.exe --zmq-port 19982`
- **Default**: 19982
- **Use case**: Integration with external test systems

**--console**

- **Purpose**: Force console output visibility
- **Usage**: `elevator.exe --console`
- **Effect**: Shows terminal window with application messages
- **Useful for**: Monitoring system status, debugging

### Common Command Line Examples

**Debug Mode for Troubleshooting:**

```
elevator.exe --debug --console
```

**Headless Mode for Server:**

```
elevator.exe --headless --http-port 8080
```

**Custom Port Configuration:**

```
elevator.exe --ws-port 18680 --http-port 19095
```

**Full Debug with Custom Ports:**

```
elevator.exe --debug --console --ws-port 18675 --http-port 19090
```

🔵 **Tip**: Command line options are particularly useful for system administrators or when running multiple instances of the application.
