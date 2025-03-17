# DBT YAML Manager

A Streamlit application for managing DBT YAML configurations. This tool provides a user-friendly interface to add, delete, and update DBT YAML setup.

## Author

**Puneet Sachdeva**

## Features

- View existing DBT YAML configurations
- Add new DBT models and their configurations
- Update existing model configurations
- Delete model configurations
- Validate YAML syntax
- Export configurations

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application using:
```bash
streamlit run app.py
```

## Structure

- `app.py`: Main Streamlit application
- `utils/yaml_manager.py`: YAML file operations utility
- `requirements.txt`: Project dependencies 