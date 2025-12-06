import json
import os

files = ['data/resumes/cand-007.json', 'data/resumes/cand-008.json']

for path in files:
    if not os.path.exists(path):
        print(f'Skipping {path} (not found)')
        continue
        
    with open(path, 'r') as f:
        data = json.load(f)
    
    modified = False
    if 'education' in data:
        for edu in data['education']:
            if 'school' in edu:
                edu['institution'] = edu.pop('school')
                modified = True
    
    if modified:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f' Fixed schema in: {path}')
    else:
        print(f'No changes needed for: {path}')
