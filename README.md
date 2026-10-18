# UniPD-CyberPhysical-Systems-And-IOT-Security-2026
This repository contains two Python projects developed for the **Cyber-Physical Systems and IoT Security** course at the University of Padua (academic year 2025/2026).

The projects reproduce and analyze two security mechanisms discussed in the scientific literature: mutual authentication for IoT devices using secure vaults, and a denial-of-service attack that exploits CAN bus error handling.

## Repository Structure
    ├── Authentication of an IoT Device and IoT Server Using Secure Vaults
    │   ├── report.pdf
    |   ├── main.py
    │   └── requirements.txt
    ├── Error Handling of In-vehicle Networks Makes Them Vulnerables/
    │   ├── report.pdf
    |   ├── main.py
    │   └── requirements.txt
    └── README.md


## Project 1: Authentication of an IoT Device and IoT Server Using Secure Vaults
This university project simulates mutual authentication between IoT devices and a server using a **Secure Vault**: a shared collection of symmetric keys whose contents are refreshed after each successful session.

The simulation also runs an **Elliptic Curve Cryptography (ECC)** authentication benchmark so that the execution time of the Secure Vault approach can be compared with a conventional public-key method.

### Simulation objectives
The project reproduces the multi-key authentication mechanism described in the accompanying report. It aims to:

- replace a single shared password with a vault containing multiple shared keys;
- mutually authenticate an IoT device and the server through a two-step challenge-response exchange;
- update the shared vault after a successful session using fresh random nonces;
- simulate several IoT devices authenticating concurrently with Python threads;
- measure the execution time of encryption, decryption, and vault synchronization; and
- compare the Secure Vault timings with an ECC-based authentication flow.

The script runs two experiments in sequence:

1. **Secure Vault authentication** — ten devices authenticate with the server. Keys selected from the shared vault are combined with XOR and used by the AES-based challenge-response protocol. The script reports the average encryption, decryption, vault-update, and total times.
2. **ECC authentication** — one device generates a random value, signs it with a NIST P-256 key, and asks the server to verify the signature. The script reports key-generation, signing, verification, and total times.

Only execution time is measured. Energy consumption, which was considered in the reference study, is outside the scope of this local Python simulation.

### Setup
The Python dependencies are listed in requirements.txt

Clone the repository or download its files, then open a terminal in the project directory.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

### Run the simulation
```powershell
py main.py
```

The program first prints the challenge-response activity for each Secure Vault device and then displays average timings in milliseconds. It subsequently runs the ECC benchmark and prints its timings. Because the protocol uses random keys and nonces and devices run in separate threads, values and message order can differ between runs.

### Project files
- main.py — Secure Vault and ECC implementations, simulation, and timing measurements.
- requirements.txt — pinned Python dependencies.
- report.pdf — project objectives, protocol description, experiment details, and results.



## Project 2: Error Handling of In-Vehicle Networks Makes Them Vulnerable
Python simulation of a **bus-off attack** against an in-vehicle Controller Area Network (CAN bus).

### Simulation objective
The project demonstrates how a malicious Electronic Control Unit (ECU) can exploit CAN error-handling behavior to disconnect a legitimate ECU from the bus.

The simulation creates two concurrent ECU nodes:

- a victim ECU, which sends CAN messages normally;
- an adversarial ECU, which uses the same message identifier but a different payload to create transmission conflicts.

Each conflict changes the ECUs' Transmit Error Counters (TECs). Both nodes initially accumulate errors, but after the victim reaches the **Error Passive** threshold, the attacker exploits the asymmetry in error handling so that its own TEC decreases while the victim's continues to rise. When the victim's TEC exceeds 254, it enters the **Bus-off** state and is disconnected from the simulated CAN bus.

The model reproduces the main behavior described in the reference study while intentionally simplifying real CAN frames, timing, arbitration, and physical-layer behavior. Its purpose is to illustrate the attack dynamics rather than emulate a complete CAN implementation.

### Setup
The Python dependencies are listed in requirements.txt

Clone the repository or download its files, then open a terminal in the project directory.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```


### Run the simulation
```powershell
py main.py
```

During execution, the terminal displays packet transmissions, current TEC values, and ECU connection changes. The simulation ends after the victim reaches the Bus-off state and is removed from the bus.

A Matplotlib window then displays the TEC evolution for the victim and attacker. The same chart is saved as `tec_plot.png` in the repository root. The expected trend is:

1. Both TEC values initially increase as conflicting frames are transmitted.
2. The victim transitions from **Error Active** to **Error Passive** at a TEC above 127.
3. The attacker's TEC begins to decrease while the victim's TEC keeps increasing.
4. The victim exceeds a TEC of 254, enters **Bus-off**, and disconnects.

### Project files
- main.py — simulation implementation and plot generation.
- requirements.txt — pinned Python dependencies.
- report.pdf — project methodology, implementation details, and comparison with the reference study.
- tec_plot.png — TEC graph generated by the simulation.
