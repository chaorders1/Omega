import os
import csv

def get_file_names_and_create_csv(folder_path):
    try:
        # Ensure the path is absolute
        abs_path = os.path.abspath(folder_path)
        
        # Check if the directory exists
        if not os.path.isdir(abs_path):
            print(f"Error: The directory '{abs_path}' does not exist.")
            return

        # Get the name of the folder
        folder_name = os.path.basename(abs_path)
        
        # Get all file names in the folder
        file_names = [f for f in os.listdir(abs_path) if os.path.isfile(os.path.join(abs_path, f))]
        
        # Create a CSV file with the same name as the folder
        csv_file_path = f"{folder_name}.csv"
        
        # Write the file names to the CSV file
        with open(csv_file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["File Name"])  # Header
            for file_name in file_names:
                writer.writerow([file_name])
        
        print(f"CSV file '{csv_file_path}' has been created with {len(file_names)} file names.")
    except PermissionError:
        print(f"Error: Permission denied to access the directory '{folder_path}'.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Example usage
if __name__ == "__main__":
    folder_path = input("Enter the folder path: ").strip()
    get_file_names_and_create_csv(folder_path)
