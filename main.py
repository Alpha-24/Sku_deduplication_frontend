import pandas as pd
from fuzzywuzzy import fuzz
from metaphone import doublemetaphone

# Load Data
def load_data(file_path):
    return pd.read_excel(file_path)

# Normalize function
def normalize_text(text):
    if isinstance(text, str):
        return ''.join(e for e in text.lower() if e.isalnum())
    return ''

# Phonetic encoding function
def phonetic_encode(text):
    if isinstance(text, str):
        primary, secondary = doublemetaphone(text)
        return primary if primary else secondary
    return ''

# Data Cleaning and Normalization
def clean_and_normalize(df):
    df['Sku_Name'] = df['Sku_Name'].astype(str)
    df['Display_Name'] = df['Display_Name'].astype(str)
    
    df['Normalized_Sku_Name'] = df['Sku_Name'].apply(normalize_text)
    df['Normalized_Display_Name'] = df['Display_Name'].apply(normalize_text)
    
    df['Phonetic_Sku_Name'] = df['Sku_Name'].apply(phonetic_encode)
    df['Phonetic_Display_Name'] = df['Display_Name'].apply(phonetic_encode)
    return df

# Compare Attributes with Scoring Out of 100
def compare_attributes(row1, row2):
    score = 0

    # Fuzzy matching for SKU Name
    sku_name_similarity = fuzz.ratio(row1['Normalized_Sku_Name'], row2['Normalized_Sku_Name'])
    score += (sku_name_similarity / 100) * 25  # Adjust weight as needed

    # Fuzzy matching for Display Name
    display_name_similarity = fuzz.ratio(row1['Normalized_Display_Name'], row2['Normalized_Display_Name'])
    score += (display_name_similarity / 100) * 25  # Adjust weight as needed
    
    # Phonetic encoding
    if row1['Phonetic_Sku_Name'] == row2['Phonetic_Sku_Name']:
        score += 15  # Adjust weight as needed
    if row1['Phonetic_Display_Name'] == row2['Phonetic_Display_Name']:
        score += 15  # Adjust weight as needed
    
    return min(score, 100)  # Ensure the score does not exceed 100

# Add reference IDs to exact duplicates
def add_ref_ids_for_exact_duplicates(df):
    unique_dict = {}
    df['ref_skuID'] = None
    df['ref_ItemID'] = None

    for idx, row in df.iterrows():
        # Key based on Normalized_Sku_Name, Normalized_Display_Name, or Item_Code
        key_sku = row['Normalized_Sku_Name']
        key_display = row['Normalized_Display_Name']
        key_code = row['Item_Code']
        
        if key_sku in unique_dict:
            df.at[idx, 'ref_skuID'] = unique_dict[key_sku]['Sku_ID']
            df.at[idx, 'ref_ItemID'] = unique_dict[key_sku]['Item_Code']
        elif key_display in unique_dict:
            df.at[idx, 'ref_skuID'] = unique_dict[key_display]['Sku_ID']
            df.at[idx, 'ref_ItemID'] = unique_dict[key_display]['Item_Code']
        elif key_code in unique_dict:
            df.at[idx, 'ref_skuID'] = unique_dict[key_code]['Sku_ID']
            df.at[idx, 'ref_ItemID'] = unique_dict[key_code]['Item_Code']
        else:
            unique_dict[key_sku] = row
            unique_dict[key_display] = row
            unique_dict[key_code] = row
    
    return df

# Identify and Handle Potential Fuzzy Duplicates
def identify_fuzzy_duplicates(df, removal_threshold=75, review_threshold=50):
    df['ref_skuID'] = df['ref_skuID'].astype('object')
    df['ref_ItemID'] = df['ref_ItemID'].astype('object')
    df['manual_review'] = False  # Initialize the manual review column
    potential_duplicates = []

    for i in range(len(df)):
        for j in range(i + 1, len(df)):
            score = compare_attributes(df.iloc[i], df.iloc[j])
            if score >= removal_threshold:
                if pd.isna(df.at[j, 'ref_skuID']) and pd.isna(df.at[j, 'ref_ItemID']):
                    df.at[j, 'ref_skuID'] = df.at[i, 'Sku_ID']
                    df.at[j, 'ref_ItemID'] = df.at[i, 'Item_Code']
                potential_duplicates.append((df.iloc[i]['Sku_ID'], df.iloc[j]['Sku_ID'], score))
            elif score >= review_threshold:
                df.at[j, 'manual_review'] = True
                potential_duplicates.append((df.iloc[i]['Sku_ID'], df.iloc[j]['Sku_ID'], score))
    
    return df, potential_duplicates

def main():
    file_path = 'data/SKU_List.xlsx'
    df = load_data(file_path)
    df = clean_and_normalize(df)
    df_with_ref_ids = add_ref_ids_for_exact_duplicates(df)
    
    # Define thresholds
    removal_threshold = 75  # Score above this will mark for reference ID
    review_threshold = 50   # Score above this will mark for manual review

    df_dedup, fuzzy_duplicates = identify_fuzzy_duplicates(
        df_with_ref_ids, 
        removal_threshold, 
        review_threshold
    )
    
    # Save deduplicated data with reference IDs and manual review flags
    df_dedup.to_excel('data/SKU_List_With_Ref_IDs.xlsx', index=False)
    
    for dup in fuzzy_duplicates:
        print(f"Potential fuzzy duplicate found: Sku_ID {dup[0]} and Sku_ID {dup[1]} with score {dup[2]}")

if __name__ == "__main__":
    main()
