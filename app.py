import streamlit as st
import yaml
from pathlib import Path
from utils.yaml_manager import YAMLManager
import json
from typing import Dict, List

# Initialize session state
if 'yaml_manager' not in st.session_state:
    st.session_state.yaml_manager = YAMLManager('dbt_configs')

def display_yaml(data):
    """Display YAML data in a formatted way."""
    st.code(yaml.dump(data, sort_keys=False, indent=2), language='yaml')

def create_column_config():
    """Create a configuration for a single column."""
    col = {}
    col1, col2 = st.columns([3, 1])
    
    with col1:
        col["name"] = st.text_input("Column Name", key=f"col_name_{st.session_state.get('col_counter', 0)}")
    with col2:
        col["tests"] = st.multiselect(
            "Tests",
            ["unique", "not_null", "positive", "relationships"],
            key=f"col_tests_{st.session_state.get('col_counter', 0)}"
        )
    
    col["description"] = st.text_area(
        "Column Description",
        key=f"col_desc_{st.session_state.get('col_counter', 0)}"
    )

    # Advanced column properties
    with st.expander("Advanced Column Properties"):
        if st.checkbox("Add Relationships", key=f"col_rel_check_{st.session_state.get('col_counter', 0)}"):
            ref_to = st.text_input(
                "References To (format: model_name.column_name)",
                key=f"col_ref_{st.session_state.get('col_counter', 0)}"
            )
            if ref_to:
                if "tests" not in col:
                    col["tests"] = []
                if isinstance(col["tests"], list):
                    col["tests"].append({
                        "relationships": {
                            "to": ref_to,
                            "field": col["name"]
                        }
                    })

        if st.checkbox("Add Custom Tests", key=f"col_custom_check_{st.session_state.get('col_counter', 0)}"):
            custom_test = st.text_input(
                "Custom Test Name",
                key=f"col_custom_{st.session_state.get('col_counter', 0)}"
            )
            if custom_test:
                if "tests" not in col:
                    col["tests"] = []
                if isinstance(col["tests"], list):
                    col["tests"].append(custom_test)

    return col

def create_model_config():
    """Create a complete model configuration using form inputs."""
    config = {}
    
    # Basic model properties
    config["description"] = st.text_area("Model Description", help="Provide a detailed description of the model")
    
    # Model materialization
    config["materialized"] = st.selectbox(
        "Materialization Type",
        ["table", "view", "incremental", "ephemeral"],
        help="Choose how the model should be materialized"
    )

    # Tags
    tags = st.text_input("Tags (comma-separated)")
    if tags:
        config["tags"] = [tag.strip() for tag in tags.split(",")]

    # Columns configuration
    st.subheader("Columns Configuration")
    
    if 'columns' not in st.session_state:
        st.session_state.columns = []
        st.session_state.col_counter = 0

    # Add new column button
    if st.button("Add Column"):
        st.session_state.col_counter += 1
        st.session_state.columns.append({})

    # Display existing columns
    columns = []
    for i, _ in enumerate(st.session_state.columns):
        st.markdown(f"#### Column {i + 1}")
        col_config = create_column_config()
        if col_config.get("name"):  # Only add if name is provided
            columns.append(col_config)

    if columns:
        config["columns"] = columns

    # Advanced model properties
    with st.expander("Advanced Model Properties"):
        # Dependencies
        if st.checkbox("Add Dependencies"):
            deps = st.text_area("Dependencies (one per line)")
            if deps:
                config["depends_on"] = {
                    "refs": [dep.strip() for dep in deps.split("\n") if dep.strip()]
                }

        # Custom properties
        if st.checkbox("Add Custom Properties"):
            custom_props = st.text_area("Custom Properties (YAML format)")
            try:
                custom_config = yaml.safe_load(custom_props)
                if custom_config:
                    config.update(custom_config)
            except yaml.YAMLError as e:
                st.error(f"Invalid YAML format: {str(e)}")

    return config

def main():
    st.title("DBT YAML Manager")
    st.sidebar.title("Navigation")

    # Navigation
    page = st.sidebar.radio(
        "Choose an action",
        ["View Configurations", "Add Model", "Update Model", "Delete Model"]
    )

    yaml_manager = st.session_state.yaml_manager

    if page == "View Configurations":
        st.header("Current DBT Configurations")
        yaml_files = yaml_manager.get_all_yaml_files()
        
        if not yaml_files:
            st.info("No YAML configurations found. Add a new model to get started!")
            return

        selected_file = st.selectbox(
            "Select a configuration file",
            yaml_files,
            format_func=lambda x: x.name
        )

        if selected_file:
            config = yaml_manager.load_yaml(selected_file)
            display_yaml(config)

    elif page == "Add Model":
        st.header("Add New Model Configuration")
        
        model_name = st.text_input("Model Name")
        file_name = st.text_input("File Name (optional)", value="")
        
        st.subheader("Model Configuration")
        
        # Use the form interface instead of raw YAML input
        config = create_model_config()
        
        # Preview the generated YAML
        if config:
            st.subheader("Preview Generated YAML")
            display_yaml(config)

        if st.button("Add Model"):
            try:
                if not model_name:
                    st.error("Model name is required!")
                    return
                    
                file_name = file_name if file_name else None
                yaml_manager.create_model(model_name, config, file_name)
                st.success(f"Model {model_name} added successfully!")
                
                # Reset the form
                st.session_state.columns = []
                st.session_state.col_counter = 0
            except Exception as e:
                st.error(f"Error: {str(e)}")

    elif page == "Update Model":
        st.header("Update Model Configuration")
        
        yaml_files = yaml_manager.get_all_yaml_files()
        if not yaml_files:
            st.info("No YAML configurations found.")
            return

        selected_file = st.selectbox(
            "Select a configuration file",
            yaml_files,
            format_func=lambda x: x.name,
            key="update_file"
        )

        if selected_file:
            config = yaml_manager.load_yaml(selected_file)
            if "models" in config and config["models"]:
                model_names = [model["name"] for model in config["models"]]
                selected_model = st.selectbox("Select model to update", model_names)
                
                current_config = next(
                    (model for model in config["models"] if model["name"] == selected_model),
                    {}
                )
                
                st.subheader("Current Configuration")
                display_yaml(current_config)
                
                st.subheader("Update Configuration")
                # Use the form interface for updates
                new_config = create_model_config()
                
                if st.button("Update Model"):
                    try:
                        yaml_manager.update_model(selected_file, selected_model, new_config)
                        st.success(f"Model {selected_model} updated successfully!")
                        # Reset the form
                        st.session_state.columns = []
                        st.session_state.col_counter = 0
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.info("No models found in the selected file.")

    elif page == "Delete Model":
        st.header("Delete Model Configuration")
        
        yaml_files = yaml_manager.get_all_yaml_files()
        if not yaml_files:
            st.info("No YAML configurations found.")
            return

        selected_file = st.selectbox(
            "Select a configuration file",
            yaml_files,
            format_func=lambda x: x.name,
            key="delete_file"
        )

        if selected_file:
            config = yaml_manager.load_yaml(selected_file)
            if "models" in config and config["models"]:
                model_names = [model["name"] for model in config["models"]]
                selected_model = st.selectbox("Select model to delete", model_names)
                
                if st.button("Delete Model", type="primary"):
                    try:
                        yaml_manager.delete_model(selected_file, selected_model)
                        st.success(f"Model {selected_model} deleted successfully!")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.info("No models found in the selected file.")

if __name__ == "__main__":
    main() 