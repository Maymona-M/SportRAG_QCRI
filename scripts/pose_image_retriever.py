import json
from pathlib import Path

class PoseImageRetriever:
    def __init__(self, db_path='images_db.json', base_dir=''):
        self.base_dir = Path(base_dir) if base_dir else Path()
        with open(db_path, 'r', encoding='utf-8') as f:
            self.images_db = json.load(f)

    def retrieve_image(self, user_query):
        query = user_query.lower()
        for key in self.images_db:
            print(f"Checking if '{key}' in query '{query}'")
            if key in query:
                img_path = self.images_db[key]
                if self.base_dir and not Path(img_path).is_absolute():
                    img_path = str(Path(self.base_dir) / img_path)
                print(f"Found match: {key} -> {img_path}")
                return img_path
        print("No image match found.")
        return None
