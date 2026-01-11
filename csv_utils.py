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


def combine_amex_restaurants(country_codes=None, output_suffix='ALL'):
    """
    Combine Amex restaurant CSV files.
    
    Args:
        country_codes (list, optional): List of country codes to combine (e.g. ['AT', 'NZ']).
                                        If None, combines all matching 'amex_restaurants_??.csv'.
        output_suffix (str): Suffix for the output file. Default is 'ALL'.
                             Output file will be 'amex_restaurants_{output_suffix}.csv'.
    """
    if country_codes:
        print(f"Combining CSV files for countries: {', '.join(country_codes)}")
        files = []
        for code in country_codes:
            f = f'amex_restaurants_{code}.csv'
            # We could check if file exists here, or let combine_csv_files handle/skip it.
            # glob might be better to verify existence, but let's just construct the list
            # and verify existence before passing to combine_csv_files if strictness is needed.
            # However, glob.glob with specific names works too.
            matches = glob.glob(f)
            if matches:
                files.extend(matches)
            else:
                print(f"Warning: File for {code} not found ({f})")
    else:
        print("Combining all country CSV files...")
        # Find all files matching the pattern amex_restaurants_??.csv
        files = glob.glob('amex_restaurants_??.csv')
    
    output_file = f'amex_restaurants_{output_suffix}.csv'
    
    if not files:
        print("No country CSV files found to combine.")
        return

    print(f"Found {len(files)} files to combine: {files}")
    combine_csv_files(files, output_file)
