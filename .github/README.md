# README Generator Automation

This repository contains an automation tool that generates interactive and styled README.md files for projects using Google's Gemini AI.

## Features

- Automatically generates README.md files for any project folder
- Uses Google Gemini AI to analyze code and create documentation
- Creates interactive READMEs with collapsible sections
- Works as a GitHub Action
- Skips folders with `.stopautomation` marker

## Setup

1. Fork or clone this repository
2. Add your Google API key as a GitHub Secret:
   - Go to repository Settings
   - Navigate to Secrets and variables → Actions
   - Create a new secret named `GOOGLEAPIKEY`
   - Add your Google API key as the value

## Usage

1. Create a new folder in the repository for your project
2. Add your project files
3. Push to the main branch
4. The automation will generate a README.md file for your project

To skip README generation for a project, create a `.stopautomation` folder in the project's root directory.

## Structure

```
.
├── automation/
│   ├── generate_readme.py
│   └── requirements.txt
├── .github/
│   └── workflows/
│       └── generate-readme.yml
└── README.md
```

## License

MIT License 
