import subprocess
import json
from typing import List, Dict
import os

class SocialHunt:
    """
    A class to search for usernames across various social media platforms using Sherlock.
    """

    def __init__(self, sherlock_path: str = "sherlock"):
        """
        Initialize the SocialHunt class.

        Args:
            sherlock_path (str): Path to the Sherlock executable. Defaults to "sherlock".
        """
        self.sherlock_path = sherlock_path

    def search(self, username: str, output_path: str = None) -> Dict[str, str]:
        """
        Search for a username across social media platforms.

        Args:
            username (str): The username to search for.
            output_path (str, optional): Path to save the results. If None, results are not saved.

        Returns:
            Dict[str, str]: A dictionary of found profiles with platform names as keys and URLs as values.
        """
        cmd = [self.sherlock_path, username, "--print-all", "--timeout", "10", "--json"]
        
        if output_path:
            cmd.extend(["--output", output_path])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            output = json.loads(result.stdout)
            return {site: data['url'] for site, data in output.items() if data['status'] == 'Claimed'}
        except subprocess.CalledProcessError as e:
            print(f"Error running Sherlock: {e}")
            return {}
        except json.JSONDecodeError:
            print("Error parsing Sherlock output")
            return {}

    @staticmethod
    def get_supported_sites() -> List[str]:
        """
        Get a list of supported social media sites.

        Returns:
            List[str]: A list of supported site names.
        """
        cmd = ["sherlock", "--list-all"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return [line.strip() for line in result.stdout.split('\n') if line.strip()]
        except subprocess.CalledProcessError as e:
            print(f"Error getting supported sites: {e}")
            return []

def main():
    """
    Main function to demonstrate the usage of SocialHunt.
    """
    hunter = SocialHunt()
    
    print("Welcome to SocialHunt!")
    username = input("Enter the username to search for: ")
    
    print("\nSearching for profiles...")
    results = hunter.search(username)
    
    if results:
        print("\nFound profiles:")
        for platform, url in results.items():
            print(f"{platform}: {url}")
    else:
        print("\nNo profiles found.")
    
    print("\nSupported sites:")
    sites = hunter.get_supported_sites()
    print(", ".join(sites))

if __name__ == "__main__":
    main()
