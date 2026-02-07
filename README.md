# Hybrid File Sharing System (Client–Server + P2P)

## Overview
This project implements a hybrid file-sharing system that combines client–server coordination with peer-to-peer (P2P) distribution. The goal is to improve reliability and availability by distributing file chunks across multiple peers while maintaining centralized tracking.

---

## Architecture
The system consists of:

* **Alice (Uploader):** Splits files into chunks.
* **Tracker:** Maintains the list of peers storing specific chunks.
* **Peers:** Store individual file segments.
* **Bob (Downloader):** Retrieves chunks from peers and reconstructs the original file.

---

## Features
* **File Chunking:** Automated segmentation of large files.
* **Distributed Storage:** Redundancy across multiple peer nodes.
* **Tracker-based Discovery:** Efficient peer lookup via a central server.
* **Peer-to-Peer Transfer:** Direct chunk transfer between nodes.
* **File Reconstruction:** Logic to reassemble chunks into the original file.

---

## Technologies
* **Python**
* **Socket Programming**
* **Client–Server Architecture**
* **Peer-to-Peer Communication**

---

## Learning Outcomes
* Understanding distributed system coordination.
* Implementing hybrid network architectures.
* Managing reliability in decentralized environments.
* Designing communication protocols between nodes.

---

## Demo
A video demonstration is available in the `/demo` folder.

## Report
Detailed design and implementation explanation is available in the `/report` folder.
