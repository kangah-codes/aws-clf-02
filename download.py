import requests
import os


def download_markdown_files():
    base_url = "https://raw.githubusercontent.com/kananinirav/AWS-Certified-Cloud-Practitioner-Notes/master/practice-exam/practice-exam-{}.md"
    output_dir = "exam_markdowns"
    os.makedirs(output_dir, exist_ok=True)

    for i in range(1, 24):
        file_url = base_url.format(i)
        file_path = os.path.join(output_dir, f"practice-exam-{i}.md")

        print(f"Downloading {file_url}...")
        response = requests.get(file_url)

        if response.status_code == 200:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"Saved: {file_path}")
        else:
            print(
                f"Failed to download {file_url} (Status: {response.status_code})")


if __name__ == "__main__":
    download_markdown_files()
