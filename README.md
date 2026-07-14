# Synesthesia Training for Adults (PyGame Implementation)

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A lightweight, **minimal-dependency** implementation of the cognitive training paradigm from **Bor et al. (2014)**, which demonstrated that adults can be trained to acquire synesthetic experiences.

This project re-creates the key behavioral tasks (Passive Drill, N-back, Delayed Match-to-Sample, and Span tasks) using only **Python** and **Pygame**, making it easy to run, modify, and distribute without installing heavy toolkits like PsychoPy or MATLAB.

## Reference
> Bor, D., Rothen, N., Schwartzman, D. J., Clayton, S., & Seth, A. K. (2014). *Adults Can Be Trained to Acquire Synesthetic Experiences.* Scientific Reports, 4, 7089.  
> [https://www.nature.com/articles/srep07089](https://www.nature.com/articles/srep07089)

## Implemented Tasks
| Task | Status | Description |
| :--- | :--- | :--- |
| **Passive Drill** | Done | Letters with associated colors are shown for passive memorization. 
| **Early Delayed Match-to-Sample** | WIP | A target graphene-color pairing is shown, then must be selected after a delay.
| **Late Delayed Match-to-Sample** | WIP |  Same as above, except initial graphene is shown in black.

## Getting Started

### Prerequisites
- Python 3.8 or higher
- `pip` (Python package installer)

### Installation
1. Clone the repository:
   ```
   git clone https://github.com/metalCrate/GCS-TRAINING.git
   cd GCS-TRAINING
2. Installing dependancies
   ```
   pip install pygame
3. To run
    ```
    python main.py
    ```
## Roadmap
* EDMTS Implementation
* LDMTS Implementation
* Early Span Implementation
* Late Span Implementation
* Letters-Colors Speed Test Implementation
* Colors-Lettersd Speed Test Implementation
* Advanced Span Implementation
* N-Back Implementation
* Backward Span Implementation
* Spelling task Implementation
* Automatic Logging of results