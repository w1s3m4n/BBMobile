import requests
from colorama import init, Fore,  Style
import json
import csv
import os

verbose = False

def clean_old_files(directory):
    """Clear the download directory of any existing files."""
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"{Fore.RED}[!] Failed to delete {file_path}. Reason: {e}")

if __name__ == "__main__":
    
    init(autoreset=True)
    
    # URL of the repository on GitHub
    repo_url = "https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/main/data"

    # List of JSON files to download
    files = [
        "bugcrowd_data.json",
        "hackerone_data.json",
        "intigriti_data.json",
        "yeswehack_data.json",
        "federacy_data.json",
        "hackenproof_data.json",
    ]

    # Directory to store the downloaded files
    download_dir = "bug_bounty_jsons"
    clean_old_files(download_dir)
    os.makedirs(download_dir, exist_ok=True)

    print(f"{Fore.BLUE}[*] Fetching data from BB Programs...")

    # Download the JSON files
    error = False
    for file in files:
        file_url = f"{repo_url}/{file}"
        response = requests.get(file_url)
        if response.status_code == 200:
            with open(os.path.join(download_dir, file), 'w') as f:
                f.write(response.text)
            print(f"    [+] Downloaded {file}")
        else:
            error = True
            print(f"    [!] Error downloading {file}")
    if error:
        print("[!] An error has raised when downloading files. Some information won't be processed. Please, check it manually.")

    # Array of dicts to save in a CSV file
    results = []

    print(f"{Fore.BLUE}[*] Processing all programs...")
    # Process the downloaded files
    for file in files:
        
        print(f"    [+] Processing {file[:-10].upper()}")

        file_path = os.path.join(download_dir, file)
        with open(file_path, 'r') as f:
            data = json.load(f)
            for program in data:
                program_name = program.get("name")
                program_url = program.get("url")
                assets = program.get("targets", {}).get("in_scope", [])
                for asset in assets:
                    
                    platform = file[:-10]
                    
                    # Money filters: We don't want retired programs or no-bounty eligible

                    if platform == "bugcrowd":
                        if program.get('max_payout') == 0:
                            continue
                    if platform == "hackerone":
                        if program.get('offers_bounties') == False:
                            continue
                    if platform == "federacy":
                        if program.get('offers_awards') == False :
                            continue
                    if platform == "hackenproof":
                        if asset.get('reward') != 'Bounty' or program.get('archived') == True:
                            continue
                    if platform == "integrity":
                        if program.get('status') != 'open' or program.get('max_bounty').get('value') == 0:
                            continue
                    if platform == "yeswehack":
                        if program.get('disabled') != 'false' or program.get('max_bounty') == 0:
                            continue
                    
                    # Bugcrowd HackenProof Integriti
                    if platform == "bugcrowd" or platform == "hackenproof" or platform == "integriti" or platform == "yeswehack":

                        asset_type = asset.get("type").lower()
                        
                        # If Yes we Hack program
                        if asset_type.startswith("mobile-application-"):
                            asset_type = asset_type.split("-")[-1].lower()
                        
                        if asset_type == "android" or asset_type == "ios":
                            if verbose:
                                print(f"    [*] Platform: {platform}")
                                print(f"    [*] Program: {program_name}")
                                print(f"    [*] Program URL: {program_url}")
                                print(f"    [*] Type: {asset_type}")
                                
                            if platform == "integriti":
                                asset = asset.get('endpoint')
                                if verbose:
                                    print(f"    [*] Asset: {asset}")

                            else:
                                asset = asset.get('target')
                                if verbose:
                                    print(f"    [*] Asset: {asset.get('target')}")

                            if verbose:
                                print("-" * 40)

                            result = {
                                    "platform": platform, 
                                    "program": program_name, 
                                    "url": program_url,
                                    "type": asset_type,
                                    "assetid": "",
                                    "instruction": asset
                                }
                            
                            results.append(result)
                    # H1
                    elif platform == "hackerone":
                        
                        asset_type = asset.get("asset_type").upper()
                        
                        try:
                            if asset_type == "OTHER":
                                if "android" in asset.get('asset_identifier').lower() or "android" in asset.get('instruction').lower():
                                    asset_type = "GOOGLE_PLAY_APP_ID"
                                elif "ios" in asset.get('asset_identifier').lower() or "ios" in asset.get('instruction').lower():
                                    asset_type = "APPLE_STORE_APP_ID"
                        except:
                            continue

                        if asset_type == "GOOGLE_PLAY_APP_ID" or asset_type == "APPLE_STORE_APP_ID":
                            
                            asset_type = 'android' if asset_type == 'GOOGLE_PLAY_APP_ID' else 'ios'
                            asset_id = asset.get('asset_identifier')
                            instruction = asset.get('instruction')
                            if verbose:
                                print(f"    [*] Platform: {platform}")
                                print(f"    [*] Program: {program_name}")
                                print(f"    [*] Program URL: {program_url}")
                                print(f"    [*] Type: {asset_type}")
                                print(f"    [*] Asset ID: {asset_id}")
                                print(f"    [*] Instruction: {instruction}")
                                print("-" * 40)
                            
                            result = {
                                    "platform": platform, 
                                    "program": program_name, 
                                    "url": program_url,
                                    "type": asset_type,
                                    "assetid": asset_id,
                                    "instruction": instruction
                                }
                            
                            results.append(result)

                    # Federacy
                    elif platform == "federacy":
                        
                        asset_type = asset.get("type").lower()
                        
                        if asset_type == "mobile":
                            
                            asset_type = 'android' if 'play.google' in asset.get('target') else 'ios'
                            asset = asset.get('target')
                            if verbose:
                                print(f"    [*] Platform: {platform}")
                                print(f"    [*] Program: {program_name}")
                                print(f"    [*] Program URL: {program_url}")
                                print(f"    [*] Type: {asset_type}")
                                print(f"    [*] Asset: {asset}")

                            result = {
                                    "platform": platform, 
                                    "program": program_name, 
                                    "url": program_url,
                                    "type": asset_type,
                                    "assetid": "",
                                    "instruction": asset
                                }
                            
                            results.append(result)

    print(f"{Fore.GREEN}[OK] Processed {len(results)} apps!")
    print(f"{Fore.BLUE}[i] Inserting results in CVS file...")

    # Export the results to a CSV file
    csv_file_path = "all_apps.csv"
    with open(csv_file_path, 'w', encoding='utf-8') as csvfile:
        fieldnames = ["platform", "program", "url", "type", "asset", "assetid", "instruction"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for result in results:
            writer.writerow(result)

    print(f"{Fore.GREEN}[OK] Done! Please check 'all_apps.csv' file to filter the results.")
    print(f"{Fore.BLUE} Happy hacking! :)")