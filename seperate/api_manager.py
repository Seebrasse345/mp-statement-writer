import configparser
import os
import importlib.util
from error_handler import log_error
from system_prompt import SYSTEM_PROMPT, REFRESH_SYSTEM_PROMPT
from tkinter import messagebox
from dotenv import load_dotenv

class ApiManager:
    """Manager for OpenAI API integration"""
    
    def __init__(self):
        self.initialize_openai()
        
    def initialize_openai(self):
        """Initialize OpenAI API with key from environment variables or config file"""
        try:
            # First check if openai is installed
            if importlib.util.find_spec("openai") is None:
                raise ImportError("The openai package is not installed")
            
            import openai
            self.openai = openai
            
            # First try to load from environment variables
            load_dotenv()
            api_key = os.getenv("OPENAI_API_KEY")
            model = os.getenv("OPENAI_MODEL", "gpt-4o")
            
            # If not found in env, look for config file
            if not api_key:
                config = configparser.ConfigParser()
                
                # Check if config file exists, if not create it
                if not os.path.exists('config.ini'):
                    config['API'] = {
                        'OPENAI_API_KEY': 'your_api_key_here',
                        'MODEL': model
                    }
                    with open('config.ini', 'w') as f:
                        config.write(f)
                    return False, "Please add your OpenAI API key in a .env file or edit the config.ini file."
                
                config.read('config.ini')
                
                if 'API' not in config:
                    config['API'] = {
                        'OPENAI_API_KEY': 'your_api_key_here',
                        'MODEL': model
                    }
                    with open('config.ini', 'w') as f:
                        config.write(f)
                
                api_key = config['API']['OPENAI_API_KEY']
                model = config['API'].get('MODEL', 'gpt-4o')
                
                if api_key == 'your_api_key_here':
                    return False, "Please add your OpenAI API key in a .env file or edit the config.ini file."
            
            openai.api_key = api_key
            self.model = model
            return True, "OpenAI API initialized successfully."
        except ImportError as e:
            log_error("OpenAI import error", e)
            return False, "The openai or dotenv package is not installed. Please run: pip install openai python-dotenv"
        except Exception as e:
            log_error("OpenAI initialization error", e)
            return False, f"Failed to initialize OpenAI API: {str(e)}"
            
    def call_llm_api(self, prompt, system_prompt=None):
        """Call the OpenAI API to generate statement"""
        try:
            if system_prompt is None:
                system_prompt = "You are an expert political communications specialist who rewrites official government statements into personalized MP communications that sound authentic, engaging, and locally relevant."
            
            response = self.openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            return True, response.choices[0].message.content.strip()
        except Exception as e:
            error_message = f"API call failed: {str(e)}"
            log_error("OpenAI API call error", e)
            return False, error_message
            
    def call_refresh_llm_api(self, prompt, system_prompt=None):
        """Call the OpenAI API to regenerate statement with feedback"""
        try:
            if system_prompt is None:
                system_prompt = "You are an expert political communications specialist who rewrites statements to sound authentic, engaging, and locally relevant."
            
            response = self.openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            return True, response.choices[0].message.content.strip()
        except Exception as e:
            error_message = f"API call failed: {str(e)}"
            log_error("OpenAI refresh API call error", e)
            return False, error_message