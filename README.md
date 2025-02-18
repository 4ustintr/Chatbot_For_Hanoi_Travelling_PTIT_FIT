# Hanoi Travel Chatbot

An AI-powered chatbot for Hanoi travel information using OpenAI's GPT model.

## Features
- Multi-language support (English, Vietnamese, Japanese)
- Travel recommendations
- Location information
- Cultural insights
- Transportation guidance

## Prerequisites
- Python 3.8+
- OpenAI API key
- Internet connection

## Installation

1. Clone the repository:
```bash
git clone https://github.com/4ustintr/Chatbot_For_Hanoi_Travelling_PTIT_FIT
cd Chatbot_For_Hanoi_Travelling_PTIT_FIT
```
2. Create virtual environment:
```bash
python3 -m venv venv

# Linux/MacOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```
3. Install dependencies:
```
pip install -r requirements.txt
```
## Environment Setup
1. Create a ```.env``` file in project root:
```
OPENAI_API_KEY=your_api_key_here
```
2. Configure your OpenAI API key in the ```.env``` file
Running the Application
Start the server:
```
python3 main.py
```
The application will be available at ```http://localhost:8000```

## Usage
Open your web browser
Navigate to ```http://localhost:8000```
Select your preferred language
Start chatting about Hanoi travel!
Contributing
Feel free to open issues and pull requests.

License
MIT License