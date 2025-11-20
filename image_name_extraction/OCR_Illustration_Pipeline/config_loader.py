"""
Utility module to load pipeline and prompt configurations.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """Load and access pipeline and prompt configurations."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize configuration loader.
        
        Args:
            base_dir: Base directory containing config files. If None, uses script directory.
        """
        if base_dir is None:
            base_dir = Path(__file__).parent
        
        self.base_dir = Path(base_dir)
        self.pipeline_config_path = self.base_dir / "pipeline_config.json"
        self.prompt_config_path = self.base_dir / "prompt_config.json"
        
        self._pipeline_config: Optional[Dict[str, Any]] = None
        self._prompt_config: Optional[Dict[str, Any]] = None
    
    @property
    def pipeline_config(self) -> Dict[str, Any]:
        """Load and cache pipeline configuration."""
        if self._pipeline_config is None:
            with open(self.pipeline_config_path, 'r', encoding='utf-8') as f:
                self._pipeline_config = json.load(f)
        return self._pipeline_config
    
    @property
    def prompt_config(self) -> Dict[str, Any]:
        """Load and cache prompt configuration."""
        if self._prompt_config is None:
            with open(self.prompt_config_path, 'r', encoding='utf-8') as f:
                self._prompt_config = json.load(f)
        return self._prompt_config
    
    def get_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Get a prompt template and optionally format it with variables.
        
        Args:
            prompt_name: Name of the prompt (e.g., 'portrait_association', 'biography_extraction', 'portrait_validation')
            **kwargs: Variables to format the prompt template with
        
        Returns:
            Formatted prompt string
        """
        prompts = self.prompt_config.get('prompts', {})
        if prompt_name not in prompts:
            raise ValueError(f"Prompt '{prompt_name}' not found in prompt_config.json")
        
        prompt_data = prompts[prompt_name]
        
        # Try to get 'template' first (new format), then fall back to 'user_prompt_template' (old format)
        prompt_template = prompt_data.get('template', prompt_data.get('user_prompt_template', ''))
        
        # Handle both string and array formats
        if isinstance(prompt_template, list):
            prompt_template = '\n'.join(prompt_template)
        
        if kwargs:
            return prompt_template.format(**kwargs)
        return prompt_template
    
    def get_prompt_config(self, prompt_name: str) -> Dict[str, Any]:
        """
        Get the full configuration for a specific prompt including temperature, format, etc.
        
        Args:
            prompt_name: Name of the prompt
        
        Returns:
            Dictionary with prompt configuration
        """
        prompts = self.prompt_config.get('prompts', {})
        if prompt_name not in prompts:
            raise ValueError(f"Prompt '{prompt_name}' not found in prompt_config.json")
        
        return prompts[prompt_name]
    
    def get_system_instruction(self, prompt_name: str) -> str:
        """
        Get the system instruction for a specific prompt.
        
        Args:
            prompt_name: Name of the prompt
        
        Returns:
            System instruction string
        """
        prompts = self.prompt_config.get('prompts', {})
        if prompt_name not in prompts:
            raise ValueError(f"Prompt '{prompt_name}' not found in prompt_config.json")
        
        system_instruction = prompts[prompt_name].get('system_instruction', '')
        
        # Handle both string and array formats
        if isinstance(system_instruction, list):
            system_instruction = '\n'.join(system_instruction)
        
        return system_instruction
    
    def get_gemini_settings(self) -> Dict[str, Any]:
        """Get Gemini model settings."""
        return self.prompt_config.get('gemini_settings', {})
    
    def get_extraction_rules(self) -> Dict[str, Any]:
        """Get extraction rules configuration."""
        return self.prompt_config.get('extraction_rules', {})


# Convenience function for quick access
def load_config(base_dir: Optional[Path] = None) -> ConfigLoader:
    """
    Load configuration files.
    
    Args:
        base_dir: Base directory containing config files
    
    Returns:
        ConfigLoader instance
    """
    return ConfigLoader(base_dir)
