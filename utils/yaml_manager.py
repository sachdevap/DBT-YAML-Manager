import yaml
import os
from typing import Dict, List, Optional, Union
from pathlib import Path

class YAMLManager:
    def __init__(self, yaml_dir: str):
        self.yaml_dir = Path(yaml_dir)
        self.yaml_dir.mkdir(parents=True, exist_ok=True)
    
    def load_yaml(self, file_path: Union[str, Path]) -> Dict:
        """Load a YAML file and return its contents."""
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file: {e}")

    def save_yaml(self, data: Dict, file_path: Union[str, Path]) -> None:
        """Save data to a YAML file."""
        with open(file_path, 'w') as f:
            yaml.dump(data, f, sort_keys=False, indent=2)

    def get_all_yaml_files(self) -> List[Path]:
        """Get all YAML files in the directory."""
        return list(self.yaml_dir.glob("*.yml")) + list(self.yaml_dir.glob("*.yaml"))

    def create_model(self, model_name: str, config: Dict, file_name: Optional[str] = None) -> str:
        """Create a new DBT model configuration."""
        if file_name is None:
            file_name = f"{model_name}.yml"
        
        file_path = self.yaml_dir / file_name
        existing_config = self.load_yaml(file_path)
        
        if "models" not in existing_config:
            existing_config["models"] = []
        
        # Check if model already exists
        for model in existing_config["models"]:
            if model.get("name") == model_name:
                raise ValueError(f"Model {model_name} already exists in {file_name}")
        
        existing_config["models"].append({"name": model_name, **config})
        self.save_yaml(existing_config, file_path)
        return str(file_path)

    def update_model(self, file_path: Union[str, Path], model_name: str, new_config: Dict) -> None:
        """Update an existing model configuration."""
        config = self.load_yaml(file_path)
        
        if "models" not in config:
            raise ValueError(f"No models found in {file_path}")
        
        for i, model in enumerate(config["models"]):
            if model.get("name") == model_name:
                config["models"][i] = {"name": model_name, **new_config}
                self.save_yaml(config, file_path)
                return
        
        raise ValueError(f"Model {model_name} not found in {file_path}")

    def delete_model(self, file_path: Union[str, Path], model_name: str) -> None:
        """Delete a model from the configuration."""
        config = self.load_yaml(file_path)
        
        if "models" not in config:
            raise ValueError(f"No models found in {file_path}")
        
        config["models"] = [m for m in config["models"] if m.get("name") != model_name]
        
        if not config["models"]:
            # If file is empty, delete it
            Path(file_path).unlink()
        else:
            self.save_yaml(config, file_path)

    def validate_yaml(self, data: Dict) -> bool:
        """Validate YAML structure for DBT configuration."""
        if not isinstance(data, dict):
            return False
        
        if "models" not in data:
            return False
        
        if not isinstance(data["models"], list):
            return False
        
        for model in data["models"]:
            if not isinstance(model, dict) or "name" not in model:
                return False
        
        return True 