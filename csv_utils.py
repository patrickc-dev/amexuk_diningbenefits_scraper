import pandas as pd
import glob

def combine_csv_files(file_paths, output_file):
    """
    Combine multiple CSV files into a single CSV file.
    
    Args:
        file_paths (list): List of file paths to the CSV files.
        output_file (str): Path to the output CSV file.
    """
    if not file_paths:
        print("No file paths provided for combination.")
        return

    try:
        combined_df = pd.DataFrame()
        
        for file in file_paths:
            try:
                df = pd.read_csv(file)
                combined_df = pd.concat([combined_df, df], ignore_index=True)
                print(f"Loaded {len(df)} rows from {file}")
            except Exception as e:
                print(f"Error reading {file}: {e}")
        
        combined_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\nSuccessfully combined {len(file_paths)} files into {output_file}")
        print(f"Total rows: {len(combined_df)}")
        
    except Exception as e:
        print(f"Error combining CSV files: {e}")


def combine_amex_restaurants():
    print("Combining all country CSV files...")
    # Find all files matching the pattern amex_restaurants_??.csv
    # We assume country codes are 2 letters, but let's be safe and grab anything that looks like a country file
    # excluding the aggregate file itself if it exists (though the pattern likely won't match ALL if we look for 2 chars)
    
    files = glob.glob('amex_restaurants_??.csv')
    output_file = 'amex_restaurants_ALL.csv'
    
    if not files:
        print("No country CSV files found to combine.")
        return

    print(f"Found {len(files)} files to combine: {files}")
    combine_csv_files(files, output_file)
