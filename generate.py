import json
import openai
import os
import subprocess
import sys
from pathlib import Path

# Main constatnts
appname = "cgai"

def recreate_structure(items, root_dir="."):
    root_path = Path(root_dir)

    for item in items:
        name = item["name"]
        item_type = item["type"]
        content = item["content"]

        path = root_path / name

        if item_type == "directory":
            path.mkdir(parents=True, exist_ok=True)

            if not isinstance(content, list):
                raise ValueError('Directory "{}" must contain a list'.format(name))

            recreate_structure(content, path)

        elif item_type == "file":
            if not isinstance(content, str):
                raise ValueError('File "{}" must contain a string'.format(name))

            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

        else:
            raise ValueError('Unknown type "{}" for "{}"'.format(item_type, name))


def recreate_structure_from_json_string(json_string, root_dir="cgai"):
    items = json.loads(json_string)

    if not isinstance(items, list):
        raise ValueError("Top-level JSON must be a list")

    recreate_structure(items, root_dir)

# Generate a source code

openai.api_key  = os.getenv('OPENAI_API_KEY')

def get_completion(prompt, model="gpt-5.4"):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]

prompt = f"""
Generate a CMake based C++ "{appname}" flkt based multiplatform application. \
The flkt package should be fetched with tag release-1.3.9. \
Include fltk_BINARY_DIR and fltk_SOURCE_DIR as a target include directories in the CMakeLists.txt \
The main function contains only one window "cgai - Hello World" with one text box "Hello, World!".\
The application can be inatalled in install root directory, not 'bin'. \
Use C++ 20.
"""
prompt = prompt + """
Return JSON list which contains:
[
  {
    "name": "CMakeLists.txt",
    "type": "file",
    "content": ??content of CMakeLists.txt??
  },
  {
    "name": "src",
    "type": "directory"
    "content": [
      {
        "name": "main.cpp",
        "type": "file",
        "content": ??content of main.cpp??
      }
    ]
  }
]
"""
print(prompt)
response = get_completion(prompt)
print(response)

root_dir = Path(appname)
build_dir = root_dir / "build"
install_dir = root_dir / "install"

recreate_structure_from_json_string(response, str(root_dir))

subprocess.run(["cmake", "-S", str(root_dir), "-B", str(build_dir)], check=True)
subprocess.run(["cmake", "--build", str(build_dir), "--config", "Release"], check=True)
subprocess.run(["cmake", "--install", str(build_dir), "--config", "Release", "--prefix", str(install_dir)], check=True)

exe_file = install_dir / appname
if sys.platform == "win32":
    exe_file = exe_file.with_suffix(".exe")

subprocess.run([str(exe_file)], check=True)
