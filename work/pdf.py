import boto3
import time
import json
import re
import os

# -------------------------------
# CONFIGURATION
# -------------------------------
LOCAL_FOLDER = "D:/aws/work/pdf_files"  # folder containing PDFs
BUCKET_NAME = "razin-textract-bucket-867927867048"
REGION = "us-east-1"

# Create the local folder if it doesn't exist
if not os.path.exists(LOCAL_FOLDER):
    os.makedirs(LOCAL_FOLDER)
    print(f"Created folder: {LOCAL_FOLDER}")

textract = boto3.client("textract", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)

# -------------------------------
# FUNCTIONS
# -------------------------------

def upload_to_s3(file_path, bucket, key):
    """Upload PDF to S3"""
    s3.upload_file(file_path, bucket, key)
    print(f"Uploaded {file_path} to s3://{bucket}/{key}")

def start_textract(bucket, document):
    """Start Textract Document Analysis"""
    response = textract.start_document_analysis(
        DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': document}},
        FeatureTypes=["TABLES", "FORMS"]
    )
    return response["JobId"]

def wait_for_job(job_id):
    """Wait until Textract job is complete"""
    while True:
        result = textract.get_document_analysis(JobId=job_id)
        status = result["JobStatus"]
        print("Job status:", status)
        if status in ["SUCCEEDED", "FAILED"]:
            break
        time.sleep(5)
    if status != "SUCCEEDED":
        raise Exception("Textract job failed")
    return result

def get_all_blocks(job_id):
    """Retrieve all blocks from Textract result"""
    all_blocks = []
    next_token = None
    while True:
        if next_token:
            result = textract.get_document_analysis(JobId=job_id, NextToken=next_token)
        else:
            result = textract.get_document_analysis(JobId=job_id)
        all_blocks.extend(result["Blocks"])
        next_token = result.get("NextToken")
        if not next_token:
            break
    return all_blocks

def extract_lines(blocks):
    """Extract LINE texts from Textract blocks"""
    return [block["Text"] for block in blocks if block["BlockType"] == "LINE" and "Text" in block]

def extract_number_from_line(line):
    """Extract the first number from a text line"""
    match = re.search(r"\d+(\.\d+)?", line)
    return match.group(0) if match else None

# -------------------------------
# MAIN AUTOMATION LOOP
# -------------------------------

for filename in os.listdir(LOCAL_FOLDER):
    if not filename.lower().endswith(".pdf"):
        continue

    local_path = os.path.join(LOCAL_FOLDER, filename)
    s3_key = filename

    # 1️⃣ Upload to S3
    upload_to_s3(local_path, BUCKET_NAME, s3_key)

    # 2️⃣ Start Textract job
    job_id = start_textract(BUCKET_NAME, s3_key)
    print(f"Started Textract job for {filename}, Job ID: {job_id}")

    # 3️⃣ Wait for Textract to finish
    result = wait_for_job(job_id)
    print(f"Textract job completed for {filename}")

    # 4️⃣ Get all blocks
    all_blocks = get_all_blocks(job_id)

    # 5️⃣ Extract text lines
    lines = extract_lines(all_blocks)

    # 6️⃣ Find indexes
    between1_start_idx = between1_end_idx = freight_terms = None
    between2_start_idx = between2_end_idx = None
    stop_list = []

    for i, text in enumerate(lines):
        lower_text = text.lower().strip()
        if "special instructions" in lower_text and between1_start_idx is None:
            between1_start_idx = i
        if "equipment & services" in lower_text and between1_end_idx is None:
            between1_end_idx = i
        if "stop" in lower_text and text not in [s[0] for s in stop_list]:
            stop_list.append((text, i))
        if "freight terms" in lower_text and freight_terms is None:
            freight_terms = i

    # 7️⃣ Print between special instructions
    if between1_start_idx is not None and between1_end_idx is not None:
        between_lines = lines[between1_start_idx + 1:between1_end_idx]
        print("=======================")
        for line in between_lines:
            print(line)
        print("=======================")

    # 8️⃣ Process all stop entries
    for stop in stop_list:
        text, idx = stop
        print("=======================")
        if idx + 5 < len(lines):
            print(f"Time: {lines[idx + 1]}")

            # Phone
            raw_phone_line = lines[idx + 2]
            match = re.search(r"\(?\d{3}\)?[ -]?\d{3}-\d{4}", raw_phone_line)
            phone_number = match.group(0) if match else raw_phone_line
            print(f"Phone: {phone_number}")

            # Address
            address_line = lines[idx + 3]
            address_parts = [part.strip() for part in address_line.split(",") if part.strip()]
            for a_idx, address in enumerate(address_parts, start=1):
                print(f"{a_idx}: {address}")

            # Comments
            selected_lines = lines[idx:len(lines)]
            comment_idx = next((i for i, t in enumerate(selected_lines) if "Items" in t), None)
            if comment_idx:
                print(f"Comment: {lines[idx + comment_idx - 1]}")
                if idx + comment_idx + 6 < len(lines):
                    print(f"{lines[idx + comment_idx + 6]}")
        print("=======================")

    # 9️⃣ Freight terms numbers
    if freight_terms and freight_terms + 9 < len(lines):
        print("=======================")
        num1 = extract_number_from_line(lines[freight_terms + 6])
        num2 = extract_number_from_line(lines[freight_terms + 9])
        print(num1 if num1 else "❌ No number found.")
        print(num2 if num2 else "❌ No number found.")
        print("=======================")

    # 10️⃣ Save Textract JSON
    json_filename = os.path.join(LOCAL_FOLDER, f"{filename}_textract.json")
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(all_blocks, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Saved full Textract result to '{json_filename}'\n\n")
