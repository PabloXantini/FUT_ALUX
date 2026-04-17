# FUT ALUX - Autonomous Soccer Robot 🤖⚽

FUT ALUX is an autonomous robotics project designed to create an omnidirectional vehicle capable of playing soccer, powered by a Finite State Machine (FSM). 

This repository hosts the complete logic of the "Brain" and features an **Advanced 2.5D Simulation Environment (Sandbox)** that allows you to test and polish the robot's autonomous responses using synthetic Computer Vision without the need to have the physical hardware connected.

---

## 🚀 Features

- **Omnidirectional Kinematics**: Factored mathematics for forward, backward, and lateral sweeping movements using force vectors.
- **FSM Intelligence**: Fully modularized cognitive structure (`Search`, `Align`, `Approach`, `Stop`).
- **Integrated Computer Vision**: Morphology, HSV masking, and contour tracking via OpenCV.
- **100% Native Sandbox Environment**:
  - Physics simulator supporting friction, wall bouncing, and rigid body occlusion between multiple agents.
  - 2.5D "Virtual Camera" Engine featuring *Painter's Algorithm* to recreate physical blind-spot visual occlusions.
  - Computationally generated Fisheye Lens Barrel Distortion using `cv2.remap` to maximize the realism of the physical sensors.

## 📦 Requirements and Installation

The repository is built on **Python 3.10+**. 
Install the main graphics and matrix computation libraries by running:

```bash
pip install numpy opencv-python pygame
```

*(Note: The engine automatically injects a mock simulation for the `RPi.GPIO` library to prevent dependency crashes when coding from environments like Windows or Mac).*

---

## 🎮 Execution Modes

The core of the project is orchestrated from the `alux.py` file. It features console arguments ready to be used:

### 1. Hardware Deployment (Real Mode)
Ideal for use inside the Raspberry Pi once physical tests are cleared. It will execute the code straight to the `L298N` motor drivers utilizing the physical camera.
```bash
python alux.py
```

### 2. Cross-Testing Sandbox Environment
Boots the Pygame window simulation where **Two Independent Artificial Intelligence Instances** (Blue Robot vs Yellow Robot) will fight for the ball.
```bash
python alux.py --sandbox
```
* **Physical Interactivity**: You can use your mouse cursor to grab the ball, drag it, and throw it to simulate physical variables. Goals scored by an artificial mouse push will be smartly ignored by the referee system.*

### 3. Visual Debugging Mode
Append the `--debug` flag to transparently reveal the system's OpenCV "visual neurons". 

If executed in Sandbox mode, it will simultaneously open two *Synthetic Virtual Camera* frames. Here you can mathematically evaluate the robots' blindness by occluding their field of view with the opponent and admire their panoramic *Fisheye* geometric deformation:

```bash
# Hardware/Real Camera Debug
python alux.py --debug

# Complete Simulator (Pygame + Multiple Computer Vision Cameras)
python alux.py --sandbox --debug
```

*(To gracefully terminate any of the visual processes, simply press the `Q` key while focusing the debugging screen).*

### 4. VSCode Integration
This repository comes with a pre-configured `.vscode/tasks.json` file. You can effortlessly run the simulation commands directly from the IDE Tasks menu:
- Open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`).
- Type and select **`Tasks: Run Task`**.
- Select your preferred task profile from the dropdown menu:
  - `Run` (Hardware mode)
  - `Run Debug` (Hardware mode with Virtual Camera)
  - `Run Sandbox` (Full 2D Simulation with Virtual Cameras)

---

## 📁 Project Architecture

The codebase strictly adheres to Clean Architecture employing the Context Injection pattern (MVC).

```text
FUT_ALUX/
├── alux.py                 # CLI Menu Orchestrator
├── fsm.py                  # Core Logic of the Finite State Machine (MContext)
├── utils/                  # [Hardware Components]
│   ├── r_context.py        # Physical wrapper and OpenCV capture treatment
│   ├── r_states.py         # Isolated Agent Behavior modules
│   ├── r_rules.py          # Trigger conditions for transitions
│   └── r_actuators.py      # Logical GPIO pins and controlled accelerations
└── sandbox/                # [Autonomous Simulation Suite]
    ├── game.py             # FPS loop, Pygame Renderer, and Robot collision handling
    ├── entities.py         # OOP definitions (Physical objects & Autonomous Entities with injected logic)
    ├── virtual_camera.py   # Numpy matrix generator engine with 2.5D Fisheye perspective
    ├── sim_context.py      # MiddleWare bridge from simulator -> fsm.py
    └── sim_actuators.py    # Catches the electrical frequencies simulating displacement 
```

## 🛠 Scaling the Intelligence
To add a new skill to the robot, simply follow the project's standard recipe:
1. Design a State in `utils/r_states.py`.
2. Invent the reacting condition in `utils/r_rules.py`.
3. Hook the transition wiring under `build_machine()` inside `alux.py`.
