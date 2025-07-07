import os
import subprocess
import logging
from urllib.parse import quote

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitURL:
    def __init__(self, repo_path=".", remote_name="origin", branch_name=None):
        self.repo_path = os.path.abspath(repo_path)  # Normalize the path
        self.remote_name = remote_name
        self.branch_name = branch_name
        self.remote_url = self._get_remote_url()
        self.repo_root = self._get_repo_root()
        self.commit_hash = self._get_commit_hash()
        if not self.branch_name:
            self.branch_name = self._get_branch_name()

    def _get_remote_url(self):
        remote_url = subprocess.check_output(
            ["git", "-C", self.repo_path, "remote", "get-url", self.remote_name],
            text=True
        ).strip()
        if remote_url.startswith("git@github.com:"):
            remote_url = remote_url.replace("git@github.com:", "https://github.com/")
        if remote_url.endswith(".git"):
            remote_url = remote_url[:-4]
        return remote_url

    def _get_repo_root(self):
        return subprocess.check_output(
            ["git", "-C", self.repo_path, "rev-parse", "--show-toplevel"],
            text=True
        ).strip()

    def _get_branch_name(self):
        return subprocess.check_output(
            ["git", "-C", self.repo_path, "rev-parse", "--abbrev-ref", "HEAD"],
            text=True
        ).strip()

    def _get_commit_hash(self):
        return subprocess.check_output(
            ["git", "-C", self.repo_path, "rev-parse", "HEAD"],
            text=True
        ).strip()

    def get(self, local_path):
        abs_path = os.path.abspath(os.path.join(self.repo_path, local_path))
        rel_path = os.path.relpath(abs_path, self.repo_root)
        encoded_path = quote(rel_path)
        latest_url = f"{self.remote_url}/blob/{self.branch_name}/{encoded_path}"
        permalink_url = f"{self.remote_url}/blob/{self.commit_hash}/{encoded_path}"
        return {
            "latest_url": latest_url,
            "permalink_url": permalink_url,
            "commit_hash": self.commit_hash
        }

    def get_size(self, local_path):
        abs_path = os.path.abspath(os.path.join(self.repo_path, local_path))
        if not os.path.isfile(abs_path):
            raise FileNotFoundError(f"{abs_path} is not a file.")
        size_bytes = os.path.getsize(abs_path)
        size_kb = size_bytes / 1024
        return f"{size_kb:.2f}"

if __name__ == "__main__":
    # Example usage
    url_gen = GitURL(
        repo_path="/Users/eller/Projects/CoastSat_Implementation/CoastSat"
    )
    result = url_gen.get("/Users/eller/Projects/CoastSat_Implementation/CoastSat/linear_models.ipynb")
    print("Latest URL:     ", result["latest_url"])
    print("Permalink URL:  ", result["permalink_url"])
    print("Commit Hash:    ", result["commit_hash"])
    size = url_gen.get_size("linear_models.ipynb")
    print("File Size:      ", size)