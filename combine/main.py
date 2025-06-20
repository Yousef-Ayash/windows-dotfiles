import os

output_file = "combined_output.txt"
base_dir = os.getcwd()  # current directory

with open(output_file, "w", encoding="utf-8") as out:
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, base_dir)
            if file == output_file:
                continue  # skip the output file itself
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                out.write(f"<-- {rel_path} -->\n")
                out.write(content + "\n\n")
            except Exception as e:
                print(f"Skipped {file_path}: {e}")
