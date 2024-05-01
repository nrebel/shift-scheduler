# Shift-Scheduler
## Description
Basic web application for creating monthwise shift schedules

## Prerequisites
Before you begin, ensure you have met the following requirements:
- macOS operating system
- Admin rights on your machine

## Installation Guide

### Step 1: Install Homebrew
Homebrew is a package manager for macOS that lets you install software directly from the command line. To install Homebrew, open your Terminal and run:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
Follow the on-screen instructions to complete the installation. After installing, you might need to add Homebrew to your system's PATH by running:
```bash
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Step 2: Install Git
Git is necessary for version control and cloning repositories. Install Git using Homebrew:
```bash
brew install git
```

### Step 3: Install Python
Install Python using Homebrew. This command will install the latest version of Python:
```bash
brew install python
```
This also installs `pip`, Python’s package installer.

### Step 4: Clone the Repository
Now, clone the GitHub repository to your local machine:
```bash
git clone https://github.com/nrebel/shift-scheduler.git
```

### Step 5: Set Up a Python Virtual Environment
Navigate into the cloned repository directory:
```bash
cd shift-scheduler
```
Create a virtual environment in this directory:
```bash
python3 -m venv venv
```
Activate the virtual environment:
```bash
source venv/bin/activate
```

### Step 6: Install Dependencies
Install any dependencies listed in a `requirements.txt` file using `pip`:
```bash
pip install -r requirements.txt
```

### Step 7: Running the Application
Run the application via
```bash
python3 run.py
```

## Usage
Access the web application via ```http://127.0.0.1:1111/index```

