# Odoo-Hackathon
# Globe Trotter Installation Guide

## Prerequisites
* Python 3.x installed on your system.
* A relational database system installed to manage user-specific itineraries, stops, and activities.

## Installation Steps

**1. Navigate to the Project Directory**
Ensure you are in the root directory of the project (`ODOO-HACKATHON`).

**2. Create a Virtual Environment**
It is recommended to use a virtual environment to keep your dependencies isolated.
```bash
python -m venv venv
```

**3. Activate the Virtual Environment**
* **Windows:**
  ```bash
  venv\Scripts\activate
  ```
* **macOS/Linux:**
  ```bash
  source venv/bin/activate
  ```

**4. Install Dependencies**
Install all required Python packages listed in the requirements file.
```bash
pip install -r requirements.txt
```

**5. Configure Environment Variables**
The project uses a `.env` file to manage sensitive configurations. 
* Open the `.env` file in the root directory.
* Fill in the necessary environment variables (e.g., database connection URIs, secret keys).

**6. Initialize the Database**
Run the database setup script to create the necessary tables for the application[cite: 1].
```bash
python DBsetup/setup.py
```

**7. Run the Application**
Start the main application server to access Globe Trotter and the initial login screen[cite: 1].
```bash
python app.py
```