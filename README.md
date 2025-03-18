# MP Statement Writer

## Overview
The MP Statement Writer is an AI-powered application designed to help Members of Parliament create unique and focused public statements. It transforms generic government communications into personalized statements that reflect local constituency concerns, specific tone preferences, and the MP's unique voice.

## Features
- **Statement Rewriting**: Transform generic government statements into personalized MP communications
- **Audience Targeting**: Customize statements for specific audience demographics
- **Tone Selection**: Choose from multiple communication tones (Formal, Empathetic, Authoritative, etc.)
- **Local Context Integration**: Incorporate constituency-specific concerns and issues
- **History Management**: Track and manage previously written statements
- **Template System**: Use past successful statements as templates for new communications
- **Import/Export**: Import previous statements and export new ones for publication

## Installation

### Prerequisites
- Python 3.8 or higher
- Tkinter (usually included with Python)
- OpenAI API key

### Setup
1. Clone this repository
```bash
git clone https://github.com/yourusername/mp-statement-writer.git
cd mp-statement-writer
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up environment variables
Create a `.env` file in the root directory with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

4. Run the application
```bash
python mp_statement_writer.py
```

## Usage

### Basic Workflow
1. Enter the original government statement in the "Raw Government Statement" field
2. Add relevant local context specific to your constituency
3. Specify the target audience for your communication
4. Select the appropriate tone for your message
5. Click "Generate Rewritten Statement" to create a personalized version
6. Review, edit if necessary, and accept the statement when satisfied
7. Export or copy the statement for publication

### Advanced Features
- **Statement History**: Access your previously generated statements from the "View" menu
- **Past Approved Statements**: View and use past successful statements as templates
- **Import Statements**: Import past statements from CSV files
- **User Guide**: Access comprehensive instructions from the Help menu

## Configuration
The application uses a `config.ini` file for configuration:

- **API Settings**: Set your OpenAI API key and preferred model
- **UI Preferences**: Adjust interface settings
- **Default Templates**: Configure default statement templates

## Development
The application is structured as follows:

- `mp_statement_writer.py`: Main application file
- `seperate/`: Directory containing modular components:
  - `api_manager.py`: Handles API communications
  - `database_manager.py`: Manages SQLite database operations
  - `error_handler.py`: Handles application errors
  - `history_manager.py`: Manages statement history
  - `ui_components.py`: Contains UI building blocks
  - `utils.py`: Utility functions

## License
[MIT License](LICENSE)

## Credits
Developed for improving MP communications with constituents. 