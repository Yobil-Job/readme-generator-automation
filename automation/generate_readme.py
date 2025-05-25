import os
import pathlib
import google.generativeai as genai
from typing import Dict, List
import mimetypes

# Configure the Gemini API key
api_key = os.environ.get("GOOGLEAPIKEY")
if not api_key:
    raise ValueError("GOOGLEAPIKEY environment variable is not set")
genai.configure(api_key=api_key)

# Constants
IGNORE_FOLDERS = ['.git', 'automation', '__pycache__', '.stopautomation']
IGNORE_FILES = ['README.md', '.env']
STOP_AUTOMATION_FOLDER = '.stopautomation'
MAX_FILE_SIZE = 100000  # 100KB
MAX_CONTENT_LENGTH = 30000  # 30KB for Gemini API

def should_ignore(path: pathlib.Path) -> bool:
    """Checks if a given path (file or folder) should be ignored."""
    if path.name in IGNORE_FOLDERS or path.name in IGNORE_FILES:
        return True
    if path.is_dir() and any(part in IGNORE_FOLDERS for part in path.parts):
        return True
    return False

def find_project_folders(root_dir: pathlib.Path) -> List[pathlib.Path]:
    """Finds potential project folders in the root directory, excluding ignored ones."""
    project_folders = []
    for item in os.scandir(root_dir):
        if item.is_dir() and not should_ignore(pathlib.Path(item.path)):
            # Check for the stop automation marker
            stop_file = pathlib.Path(item.path) / STOP_AUTOMATION_FOLDER
            if not stop_file.exists():
                project_folders.append(pathlib.Path(item.path))
            else:
                print(f"Skipping folder {item.path} due to {STOP_AUTOMATION_FOLDER} folder.")
    return project_folders

def is_text_file(file_path: pathlib.Path) -> bool:
    """Check if a file is likely to be a text file."""
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type and mime_type.startswith('text/'):
        return True
    # Common text file extensions
    text_extensions = {'.py', '.js', '.ts', '.html', '.css', '.md', '.txt', '.json', '.xml', '.yaml', '.yml', '.sh', '.bat', '.ps1'}
    return file_path.suffix.lower() in text_extensions

def read_project_files(project_folder: pathlib.Path) -> Dict[str, str]:
    """Recursively reads files in a project folder, ignoring specified ones."""
    file_contents = {}
    for root, _, files in os.walk(project_folder):
        current_dir = pathlib.Path(root)
        if should_ignore(current_dir):
            continue
        for file in files:
            file_path = current_dir / file
            if not should_ignore(file_path) and is_text_file(file_path):
                try:
                    # Check file size
                    if file_path.stat().st_size > MAX_FILE_SIZE:
                        print(f"File {file_path} is too large, skipping...")
                        continue
                        
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Truncate content if too long
                        if len(content) > MAX_CONTENT_LENGTH:
                            content = content[:MAX_CONTENT_LENGTH] + "\n... (content truncated due to length)"
                        file_contents[str(file_path)] = content
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
    return file_contents

def generate_readme_with_gemini(file_contents: Dict[str, str]) -> str:
    """Sends file contents to Gemini API and generates README content."""
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-1.0-pro')
        
        # Prepare the base prompt
        base_prompt = """Please analyze the following project files and generate a comprehensive README.md file.
        The README should be in Markdown format with inline HTML for interactive elements.
        
        Required sections:
        1. Project Overview - A clear description of what the project does
        2. Features - List of main features and capabilities
        3. Installation - How to install and set up the project
        4. Usage - How to use the project with examples
        5. Example Code Snippets - If applicable, show some code examples
        6. License - Include license information if available
        
        Use HTML elements like <details> for collapsible sections to make it interactive.
        Make the README professional, well-structured, and easy to understand.
        
        Project files:
        """
        
        prompt = base_prompt
        
        # Add file contents to the prompt, checking total length
        for file_path, content in file_contents.items():
            file_block = f"\n\nFile: {file_path}\nContent:\n{content}\n"
            # Check if adding this file block exceeds the max content length
            if len(prompt) + len(file_block) > MAX_CONTENT_LENGTH:
                print(f"Warning: Skipping file {file_path} because adding its content would exceed the total prompt length limit.")
                # Optionally, could truncate the file_block further here if needed
                break # Stop adding files if the limit is reached
                
            prompt += file_block
        
        # Add a message if files were skipped
        if len(prompt) == len(base_prompt):
             prompt += "\n\nNo file contents were included in the prompt due to size limitations or no relevant files being found."
        elif len(prompt) < sum(len(f"\n\nFile: {fp}\nContent:\n{content}\n") for fp, content in file_contents.items()) + len(base_prompt):
             prompt += "\n\n... (some file contents were skipped due to total prompt length limitations)"


        # Generate content
        response = model.generate_content(prompt)
        
        if not response.text:
            # If response is still empty, it might be another issue, but we should return something informative
            print("Gemini API returned an empty response even after prompt truncation.")
            return f"# Error Generating README\n\nAn error occurred while generating the README: Received empty response from Gemini API. Prompt length: {len(prompt)}"
            
        return response.text
        
    except Exception as e:
        print(f"Error generating README with Gemini: {e}")
        return f"# Error Generating README\n\nAn error occurred while generating the README: {str(e)}"

def save_readme(project_folder: pathlib.Path, readme_content: str) -> None:
    """Saves the generated README content to the project folder."""
    readme_path = project_folder / 'README.md'
    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"README.md generated successfully in {project_folder}")
    except Exception as e:
        print(f"Error saving README.md to {project_folder}: {e}")

def main():
    """Main function to run the README generation process."""
    root_directory = pathlib.Path(__file__).parent.parent  # Assumes script is in automation/
    project_folders = find_project_folders(root_directory)

    if not project_folders:
        print("No valid project folders found.")
        return

    for project_folder in project_folders:
        print(f"Processing folder: {project_folder}")
        file_contents = read_project_files(project_folder)
        if file_contents:
            readme_content = generate_readme_with_gemini(file_contents)
            save_readme(project_folder, readme_content)
        else:
            print(f"No relevant files found in {project_folder}. Skipping README generation.")

if __name__ == "__main__":
    main()
