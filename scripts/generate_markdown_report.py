import argparse
import sys
from pathlib import Path
from typing import List, Optional

def generate_report(output_file: str, text_output: Optional[str], images: List[str]):
    report = "# Financial Analysis Demo Report\n\n"
    
    # Add text output
    if text_output:
        report += "## Analysis Output\n\n"
        report += "```\n"
        try:
            path = Path(text_output)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    report += f.read()
            else:
                report += "Text output file not found.\n"
        except Exception as e:
            report += f"Error reading text output: {e}\n"
        report += "\n```\n\n"
    
    # Add images
    if images:
        report += "## Visualizations\n\n"
        found_images = False
        for img in images:
            if not img: continue
            path = Path(img)
            if path.exists():
                found_images = True
                report += f"### {path.stem.replace('_', ' ').title()}\n\n"
                report += f"![{path.name}]({path.name})\n\n"
        
        if not found_images:
            report += "No visualizations generated.\n\n"
    
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report generated at {output_file}")
    except Exception as e:
        print(f"Failed to write report: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Generate Markdown report from demo outputs")
    parser.add_argument("--output", default="demo_report.md", help="Output markdown file")
    parser.add_argument("--text", help="Path to text output file")
    parser.add_argument("--images", nargs="*", default=[], help="List of image files")
    
    args = parser.parse_args()
    
    generate_report(args.output, args.text, args.images)

if __name__ == "__main__":
    main()