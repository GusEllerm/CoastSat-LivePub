# CoastSat-LivePub ~ Under Development

This repository combines the [CoastSat](https://github.com/kvos/CoastSat) coastal remote sensing workflow with a custom module (`LP_Crate/`) designed to generate an interface RO-Crate describing the experiment's structure and metadata.

## 📁 Repository Structure

```
CoastSat_Implementation/
├── CoastSat/      	# CoastSat source code (as a Git submodule)
├── LP_Crate/      	# Custom logic for generating interface.crate
├── Micropublication/ 	# Early logic for generating Micropublications
├── .gitmodules    	# Git submodule configuration
└── README.md
```

## 🚀 Getting Started

### 1. Clone the repository **with submodules**

```bash
git clone --recurse-submodules https://github.com/YOUR_USERNAME/CoastSat_Implementation.git
cd CoastSat_Implementation
```

> 🔄 If you've already cloned without `--recurse-submodules`, run:

```bash
git submodule update --init --recursive
```

---

### 2. Working with CoastSat

To update the CoastSat submodule to the latest version:

```bash
cd CoastSat
git checkout main         # or master, depending on branch
git pull origin main
cd ..
git commit -am "Update CoastSat submodule"
```

---

### 3. About `LP_Crate`

The `LP_Crate/` directory contains logic for generating a LivePublication-compatible interface crate (`interface.crate`) that documents the structure and execution of the CoastSat workflow.

---

## 📄 License

This repository follows the licensing terms of its constituent parts. See `CoastSat/LICENSE` for details about the CoastSat component.
