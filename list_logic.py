import re
import pandas as pd
from pdfminer.layout import LAParams, LTTextContainer
from pdfminer.high_level import extract_pages
from openpyxl import Workbook
import fitz

def extract_lists(pdf_file):
    bullet_patterns = ("*", "-", "•", "o", "❖", "⬛", "◻", "☐", "→", "»", "P", "•", "●", "● ●", "■")
    all_lists = []

    for page_layout in extract_pages(pdf_file):
        current_list = []
        list_started = False
        pattern = r'^([A-Za-z]\)|\d\)|\d\.|[A-Za-z]\.|[A-Za-z]|\d)(.+)\S'

        for element in page_layout:
            if isinstance(element, LTTextContainer):
                text = element.get_text().strip()
                if text:
                    if text.startswith(bullet_patterns) or re.match(pattern, text):
                        if not list_started:
                            list_started = True
                        current_list.append(text)
                    elif list_started:
                        list_started = False
                        all_lists.append(current_list)
                        current_list = []

        if current_list:
            all_lists.append(current_list)

    return all_lists

def filter_list_items(df):
    list_pattern_1 = r'^([*+\-•o❖⬛◻☐→»]|[a-zA-Z\d]+[.][a-zA-Z\d]+)\s(.+)'
    list_pattern_2 = r'^([*+\-•o❖⬛◻☐→»●● ●]|[a-zA-Z\d]+[.])\s(.+)'
    unwanted_pattern = r'^\d+\.\d+\s×\s10\^(-?\d+)\s(?:[a-zA-Z\d]+){1,2}$'

    valid_list_items = []

    for index, row in df.iterrows():
        text = str(row["List Items"])  # Replace with the actual column name
        match_1 = re.match(list_pattern_1, text)
        match_2 = re.match(list_pattern_2, text)
        unwanted_match = re.match(unwanted_pattern, text)

        if (match_1 or match_2) and not unwanted_match and len(text) >= 10:
            valid_list_items.append(text)

    df_filtered = pd.DataFrame({"Filtered List Items": valid_list_items})
    return df_filtered

def add_boundary_box_to_pdf(input_pdf_path, target_texts, output_pdf_path, color=(1, 0, 0), csv_filename=None):
    doc = fitz.open(input_pdf_path)
    bounding_boxes = []
    bounding_box_page_num = []

    for page_num in range(doc.page_count):
        page = doc[page_num]

        for target_text in target_texts:
            text_instances = page.search_for(target_text)

            if text_instances:
                min_x0 = min_y0 = float('inf')
                max_x1 = max_y1 = float('-inf')

                for rect in text_instances:
                    x0, y0, x1, y1 = rect.x0, rect.y0, rect.x1, rect.y1
                    min_x0 = min(min_x0, x0)
                    min_y0 = min(min_y0, y0)
                    max_x1 = max(max_x1, x1)
                    max_y1 = max(max_y1, y1)

                combined_rect = fitz.Rect(min_x0, min_y0, max_x1, max_y1)
                bounding_boxes.append((page_num, min_x0, min_y0, max_x1, max_y1))
                bounding_box_page_num.append(page_num)
                page.draw_rect(combined_rect, color)

    doc.save(output_pdf_path)
    doc.close()

    df = pd.DataFrame({
        'PageNumber': bounding_box_page_num,
        'X0': [box[1] for box in bounding_boxes],
        'Y0': [box[2] for box in bounding_boxes],
        'X1': [box[3] for box in bounding_boxes],
        'Y1': [box[4] for box in bounding_boxes]
    })

    if csv_filename:
        df.to_csv(csv_filename, index=False)

def modify_csv_format(original_csv_path, new_csv_path):
    try:
        # Load the original CSV file
        df = pd.read_csv(original_csv_path)

        # Create a new DataFrame with the modified format
        new_df = pd.DataFrame({
            'pagenumber': df['PageNumber'],
            'Left': df['X0'],
            'Top': df['Y0'],
            'Width': df['X1'] - df['X0'],
            'Height': df['Y1'] - df['Y0']
        })

        # Save the new DataFrame to a new CSV file
        new_df.to_csv(new_csv_path, index=False)

        print("Modified CSV file saved to", new_csv_path)
    except Exception as e:
        print("An error occurred:", str(e))

if __name__ == "__main__":
    # Step 1: Extract lists from the PDF
    pdf_file = r"input/sample_1.pdf"
    all_lists = extract_lists(pdf_file)
    flattened_lists = [item for sublist in all_lists for item in sublist]

    df = pd.DataFrame({"List Items": flattened_lists})

    # Step 2: Filter the list items
    df_filtered = filter_list_items(df)
    df_filtered.to_excel("filtered_lists.xlsx", index=False)

    # Step 3: Add bounding boxes to the PDF
    excel_file_path = "filtered_lists.xlsx"
    df_target_text = pd.read_excel(excel_file_path)
    target_text = df_target_text['Filtered List Items'].tolist()
    input_pdf_path = "input/sample_1.pdf"
    output_pdf_path = "output.pdf"
    csv_filename = "combined_bounding_boxes.csv"

    add_boundary_box_to_pdf(input_pdf_path, target_text, output_pdf_path, csv_filename=csv_filename)
    original_csv_path = 'combined_bounding_boxes.csv'
    new_csv_path = 'modified_final.csv'
    modify_csv_format(original_csv_path, new_csv_path)
