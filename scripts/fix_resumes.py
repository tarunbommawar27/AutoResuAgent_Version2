import json
import os

# Files to fix
files_to_fix = [
    "data/resumes/cand-007.json",
    "data/resumes/cand-008.json"
]

def fix_resume_keys():
    for file_path in files_to_fix:
        if not os.path.exists(file_path):
            print(f"Skipping {file_path} (not found)")
            continue
            
        try:
            # 1. Read the JSON
            with open(file_path, "r") as f:
                data = json.load(f)
            
            # 2. Fix the keys
            modified = False
            if "education" in data:
                for edu in data["education"]:
                    if "school" in edu:
                        # Rename 'school' to 'institution'
                        edu["institution"] = edu.pop("school")
                        modified = True
            
            # 3. Save back to disk
            if modified:
                with open(file_path, "w") as f:
                    json.dump(data, f, indent=2)
                print(f"✅ Fixed schema in: {file_path}")
            else:
                print(f"No changes needed for: {file_path}")
                
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")

if __name__ == "__main__":
    fix_resume_keys()