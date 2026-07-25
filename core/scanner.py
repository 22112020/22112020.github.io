from pathlib import Path

class LunaScanner:
    def __init__(self, project_path="."):
        self.root = Path(project_path)

    def scan(self):
        folders = [
            "pasaran_luna",
            "data_harian",
            "rules",
            "engines",
            "reports",
            "config"
        ]

        result = {
            "project": str(self.root),
            "folders": {},
            "engines": []
        }

        for folder in folders:
            result["folders"][folder] = (self.root / folder).exists()

        engine_path = self.root / "engines"
        if engine_path.exists():
            result["engines"] = [
                x.name for x in engine_path.iterdir()
                if x.is_dir()
            ]

        return result


def show_scan(result):
    print("\n========== LUNA CORE SCANNER ==========")
    print("Project:", result["project"])

    print("\nFolders:")
    for name, exists in result["folders"].items():
        print(("✓" if exists else "✗"), name)

    print("\nEngines:")
    if result["engines"]:
        for e in result["engines"]:
            print("✓", e)
    else:
        print("- belum ada engine")

    print("\nScanner selesai")
