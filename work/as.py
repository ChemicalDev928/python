import boto3
import time
import json

# -------------------------------
# AWS & FILE CONFIG
# -------------------------------
BUCKET_NAME = "razin-textract-bucket-867927867048"
DOCUMENT_NAME = "sample.pdf"
REGION = "us-east-1"

print("📤 Starting Textract job...")

textract = boto3.client("textract", region_name=REGION)

# -------------------------------
# 1️⃣ Start Textract Job
# -------------------------------
response = textract.start_document_analysis(
    DocumentLocation={"S3Object": {"Bucket": BUCKET_NAME, "Name": DOCUMENT_NAME}},
    FeatureTypes=["TABLES", "FORMS"]
)
job_id = response["JobId"]
# print("🆔 Job started with ID:", job_id)

# -------------------------------
# 2️⃣ Wait for Completion
# -------------------------------
while True:
    result = textract.get_document_analysis(JobId=job_id)
    status = result["JobStatus"]
    print("⏳ Job status:", status)
    if status in ["SUCCEEDED", "FAILED"]:
        break
    time.sleep(5)

if status != "SUCCEEDED":
    print("❌ Textract job failed.")
    exit()

# -------------------------------
# 3️⃣ Collect All Pages
# -------------------------------
all_blocks = []
next_token = None
while True:
    if next_token:
        result = textract.get_document_analysis(JobId=job_id, NextToken=next_token)
    all_blocks.extend(result["Blocks"])
    next_token = result.get("NextToken")
    if not next_token:
        break

# -------------------------------
# 4️⃣ Extract lines between two keywords
# -------------------------------
chain_list = change_list = ["Comments"]

for i, block in enumerate(all_blocks):
    if block["BlockType"] == "LINE" and block.get("Text") in change_list:
        # Find next line after 'Comments'
        for j in range(i + 1, len(all_blocks)):
            next_block = all_blocks[j]
            if next_block["BlockType"] == "LINE":
                print(f"➡️ After '{block['Text']}': {next_block['Text']}")
                break

# Collect all LINE blocks
lines = [block["Text"] for block in all_blocks if block["BlockType"] == "LINE" and "Text" in block]

between1_start_idx = between1_end_idx = None
between2_start_idx = between2_end_idx = None

for i, text in enumerate(lines):
    lower_text = text.lower().strip()
    if "special instructions" in lower_text and between1_start_idx is None:
        between1_start_idx = i
    if "equipment & services" in lower_text and between1_end_idx is None:
        between1_end_idx = i
    if "stop 1" in lower_text and between2_start_idx is None:
        between2_start_idx = i
    if "stop 2" in lower_text and between2_end_idx is None:
        between2_end_idx = i

# -------------------------------
# 4a️⃣ Between "Special Instructions" and "Equipment & Services"
# -------------------------------
if between1_start_idx is not None and between1_end_idx is not None and between1_start_idx < between1_end_idx:
    between_lines = lines[between1_start_idx + 1:between1_end_idx]
    if between_lines:
        print("✅ Text between 'Special Instructions' and 'Equipment & Services':\n")
        for line in between_lines:
            print(line)
    else:
        print("⚠️ No text found between the two sections.")
else:
    print("⚠️ Could not find both 'Special Instructions' and 'Equipment & Services' or they appear in reverse order.")

# -------------------------------
# 4b️⃣ Between "Stop 1" and "Stop 2" — stop before "Items"
# -------------------------------
import re

# -------------------------------
# 4b️⃣ Between "Stop 1" and "Stop 2" — stop before "Items"
# -------------------------------
if between2_start_idx is not None and between2_end_idx is not None and between2_start_idx < between2_end_idx:
    between_lines = lines[between2_start_idx + 1:between2_end_idx]

    # Stop collecting once "Items" appears
    filtered_lines = []
    for text in between_lines:
        if "items" in text.lower():
            break
        filtered_lines.append(text.strip())

    if filtered_lines:
        print("\n✅ Text between 'Stop 1' and 'Stop 2' (until 'Items'):\n")
        for text in filtered_lines:
            print(text)

        # -------------------------------
        # 🧠 Extract the specific details
        # -------------------------------
        phone = company = address = door = city = state = zipcode = comment = None

        # 1️⃣ Find phone number (e.g. (770) 601-6427)
        phone_pattern = re.compile(r"\(\d{3}\)\s*\d{3}-\d{4}")
        for text in filtered_lines:
            match = phone_pattern.search(text)
            if match:
                phone = match.group(0)
                break

        # 2️⃣ Find company/address line (next line after phone)
        if phone:
            phone_idx = next(i for i, t in enumerate(filtered_lines) if phone in t)
            if phone_idx + 1 < len(filtered_lines):
                address_line = filtered_lines[phone_idx + 1]
                parts = [p.strip() for p in address_line.split(",")]

                if len(parts) >= 1:
                    company = parts[0]  # e.g. "Mattress Firm"
                if len(parts) >= 2:
                    address = parts[1]  # e.g. "12002 Volunteer Blvd Door 40"
                    # check if "Door" exists
                    door_match = re.search(r"Door\s*\d+", address)
                    if door_match:
                        door = door_match.group(0)
                        address = address.replace(door, "").strip()
                if len(parts) >= 3:
                    city = parts[2]
                if len(parts) >= 4:
                    state = parts[3]

        # 3️⃣ Find ZIP code
        for text in filtered_lines:
            zip_match = re.search(r"\b\d{5}(?:-\d{4})?\b", text)
            if zip_match:
                zipcode = zip_match.group(0)
                break

        # 4️⃣ Find "Comments"
        for text in filtered_lines:
            if "comments" in text.lower():
                comment = "Comments"
                break

        # -------------------------------
        # ✅ Print parsed results
        # -------------------------------
        print("\n📦 Extracted Info:")
        print(f"📞 Phone: {phone}")
        print(f"🏢 Company: {company}")
        print(f"📍 Address: {address}")
        print(f"🚪 Door: {door}")
        print(f"🏙️ City: {city}")
        print(f"🗺️ State: {state}")
        print(f"📮 ZIP: {zipcode}")
        print(f"🗒️ Comment keyword: {comment}")




        print("\n📊 Extracting table data...\n")

        block_map = {b["Id"]: b for b in all_blocks}
        text_map = {b["Id"]: b["Text"] for b in all_blocks if "Text" in b}

        table_data = []
        for block in all_blocks:
            if block["BlockType"] == "CELL":
                row = block.get("RowIndex", 0)
                col = block.get("ColumnIndex", 0)
                cell_text = ""

                if "Relationships" in block:
                    for rel in block["Relationships"]:
                        if rel["Type"] == "CHILD":
                            for cid in rel["Ids"]:
                                if cid in text_map:
                                    cell_text += text_map[cid] + " "

                table_data.append((row, col, cell_text.strip()))

        # Sort by row and column
        table_data.sort(key=lambda x: (x[0], x[1]))

        # Print all table data
        for row, col, text in table_data:
            print(f"Row {row}, Col {col}: {text}")


        target_row = 3
        target_col = 2

        specific_cell = next(
            (text for (row, col, text) in table_data if row == target_row and col == target_col),
            None
        )


    else:
        print("⚠️ No text found between the two sections (before 'Items').")
else:
    print("⚠️ Could not find both 'Stop 1' and 'Stop 2' or they appear in reverse order.")

# -------------------------------
# 5️⃣ Extract table data (optional)
# -------------------------------

# -------------------------------
# 6️⃣ Extract specific cell value (example: Row 2, Col 2)
# -------------------------------

if specific_cell:
    print(f"\n🎯 Value at Row {target_row}, Col {target_col}: {specific_cell}")
else:
    print(f"\n⚠️ No data found at Row {target_row}, Col {target_col}")


























import boto3
import time

BUCKET_NAME = "razin-textract-bucket-867927867048"
DOCUMENT_NAME = "sample.pdf"
REGION = "us-east-1"

textract = boto3.client("textract", region_name=REGION)

# --- Step 1: Start the job ---
response = textract.start_document_analysis(
    DocumentLocation={"S3Object": {"Bucket": BUCKET_NAME, "Name": DOCUMENT_NAME}},
    FeatureTypes=["TABLES", "FORMS"]
)
job_id = response["JobId"]
print(f"🆔 Started job: {job_id}")

# --- Step 2: Wait for completion ---
while True:
    result = textract.get_document_analysis(JobId=job_id)
    status = result["JobStatus"]
    print("Job status:", status)
    if status in ["SUCCEEDED", "FAILED"]:
        break
    time.sleep(5)

if status != "SUCCEEDED":
    raise RuntimeError("❌ Textract job failed.")

# --- Step 3: Get all pages ---
all_blocks = []
next_token = None
while True:
    if next_token:
        result = textract.get_document_analysis(JobId=job_id, NextToken=next_token)
    all_blocks.extend(result["Blocks"])
    next_token = result.get("NextToken")
    if not next_token:
        break

# --- Step 4: Extract only line texts ---
lines = [block["Text"] for block in all_blocks if block["BlockType"] == "LINE" and "Text" in block]

# --- Step 5: Helper function ---
def extract_between(lines, start_key, end_key):
    """
    Extracts all lines between start_key and end_key (case-insensitive)
    """
    start_key = start_key.lower().strip()
    end_key = end_key.lower().strip()

    try:
        start_idx = next(i for i, l in enumerate(lines) if start_key in l.lower())
        end_idx = next(i for i, l in enumerate(lines) if end_key in l.lower() and i > start_idx)
        return lines[start_idx + 1:end_idx]
    except StopIteration:
        return []

# --- Step 6: Examples of extraction ---
between_special = extract_between(lines, "special instructions", "equipment & services")
between_stop = extract_between(lines, "stop 1", "stop 2")

# --- Step 7: Output ---
def print_section(title, data):
    if data:
        print(f"\n========= {title} =========")
        print("\n".join(data))
        print("===========================")

print_section("Special Instructions → Equipment & Services", between_special)
print_section("Stop 1 → Stop 2", between_stop)
















import boto3
import time
import json
import re

BUCKET_NAME = "razin-textract-bucket-867927867048"
DOCUMENT_NAME = "sample.pdf"
REGION = "us-east-1"

textract = boto3.client("textract", region_name=REGION)

response = textract.start_document_analysis(
    DocumentLocation={"S3Object": {"Bucket": BUCKET_NAME, "Name": DOCUMENT_NAME}},
    FeatureTypes=["TABLES", "FORMS"]
)
job_id = response["JobId"]

while True:
    result = textract.get_document_analysis(JobId=job_id)
    status = result["JobStatus"]
    print("Job status:", status)
    if status in ["SUCCEEDED", "FAILED"]:
        break
    time.sleep(5)

if status != "SUCCEEDED":
    print("❌ Textract job failed.")
    exit()

all_blocks = []
next_token = None
while True:
    if next_token:
        result = textract.get_document_analysis(JobId=job_id, NextToken=next_token)
    all_blocks.extend(result["Blocks"])
    next_token = result.get("NextToken")
    if not next_token:
        break

chain_list = change_list = ["Comments"]

for i, block in enumerate(all_blocks):
    if block["BlockType"] == "LINE" and block.get("Text") in change_list:
        # Find next line after 'Comments'
        for j in range(i + 1, len(all_blocks)):
            next_block = all_blocks[j]
            if next_block["BlockType"] == "LINE":
                print("============================")
                print(f"{next_block['Text']}")
                print("============================")
                break

lines = [block["Text"] for block in all_blocks if block["BlockType"] == "LINE" and "Text" in block]

between1_start_idx = between1_end_idx = between2_start_idx = between2_end_idx = freight_terms = None

for i, text in enumerate(lines):
    lower_text = text.lower().strip()
    if "special instructions" in lower_text and between1_start_idx is None:
        between1_start_idx = i
    if "equipment & services" in lower_text and between1_end_idx is None:
        between1_end_idx = i
    if "stop 1" in lower_text and between2_start_idx is None:
        between2_start_idx = i
    if "stop 2" in lower_text and between2_end_idx is None:
        between2_end_idx = i
    if "freight terms" in lower_text and freight_terms is None:
        freight_terms = i

if between1_start_idx is not None and between1_end_idx is not None and between1_start_idx < between1_end_idx:
    between_lines = lines[between1_start_idx + 1:between1_end_idx]
    if between_lines:
        print("=======================")
        for line in between_lines:
            print(line)
        print("=======================")

if (
    between2_start_idx is not None
    and between2_end_idx is not None
    and between2_start_idx < between2_end_idx
):
    between_lines = lines[between2_start_idx + 1 : between2_end_idx]
    if between_lines:
        print("=======================")
        # print(between2_start_idx)
        
        if between2_start_idx < len(lines):
            # Time
            print(f"Time: {lines[between2_start_idx + 1]}")

            # Extract clean phone
            raw_phone_line = lines[between2_start_idx + 2]
            match = re.search(r"\(?\d{3}\)?[ -]?\d{3}-\d{4}", raw_phone_line)
            if match:
                phone_number = match.group(0)
                print(f"Phone: {phone_number}")
            else:
                print(f"Phone: {raw_phone_line}")
            
            # address
            # print(f"Address: {lines[between2_start_idx+3]}")

            # Address
            address_line = lines[between2_start_idx + 3]
            address_parts = [part.strip() for part in address_line.split(",") if part.strip()]
            for idx, address in enumerate(address_parts, start=1):
                print(f"{idx}: {address}")
            print(f"{lines[between2_start_idx + 4]}")
            selected_lines = lines[between2_start_idx:len(lines)]
            commnet_number = 0
            for i, text in enumerate(selected_lines, start=between2_start_idx):
                if "Items" in text:
                    commnet_number = i - between2_start_idx - 1
            print(f"Comment: {lines[between2_start_idx + commnet_number]}")
            # print(f"Comment: {lines[between2_start_idx + 5]}")
            print(f"{lines[between2_start_idx + commnet_number+7]}")
        else:
            print(f"❌ Only {len(lines)} lines available.")
        print("=======================")

if (
    between2_end_idx is not None
    and len(lines) is not None
    and between2_end_idx < len(lines)
):
    between_lines = lines[between2_end_idx + 1 : len(lines)]
    if between_lines:
        print("=======================")
        print(between2_start_idx)
        
        if between2_end_idx < len(lines):
            # Time
            print(f"Time: {lines[between2_end_idx + 1]}")

            # Extract clean phone
            raw_phone_line = lines[between2_end_idx + 2]
            match = re.search(r"\(?\d{3}\)?[ -]?\d{3}-\d{4}", raw_phone_line)
            if match:
                phone_number = match.group(0)
                print(f"Phone: {phone_number}")
            else:
                print(f"Phone: {raw_phone_line}")
            address_line = lines[between2_end_idx + 3]
            address_parts = [part.strip() for part in address_line.split(",") if part.strip()]
            for idx, address in enumerate(address_parts, start=1):
                print(f"{idx}: {address}")
            selected_lines = lines[between2_end_idx:len(lines)]
            commnet_number = 0
            for i, text in enumerate(selected_lines, start=between2_end_idx):
                if "Items" in text:
                    commnet_number = i - between2_end_idx - 1
            print(f"Comment: {lines[between2_end_idx + commnet_number]}")
            print(f"{lines[between2_end_idx + commnet_number+7]}")
        else:
            print(f"❌ Only {len(lines)} lines available.")
        print("=======================")

if (
    freight_terms is not None
    and len(lines) is not None
    and freight_terms < len(lines)
):
    between_lines = lines[freight_terms + 1 : len(lines)]
    if between_lines:
        print("=======================")
        match_1 = re.search(r"\d+(\.\d+)?", lines[freight_terms+6])
        match_2 = re.search(r"\d+(\.\d+)?", lines[freight_terms+9])
        if match_1:
            number = match_1.group(0)
            print(number)
        else:
            print("❌ No number found.")
        print("=======================")
        if match_2:
            number = match_2.group(0)
            print(number)
        else:
            print("❌ No number found.")
        print("=======================")