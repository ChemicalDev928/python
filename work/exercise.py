import boto3
import os
import time
import re

# -------------------------------
# CONFIGURATION
# -------------------------------
LOCAL_FOLDER = "D:/aws/work/"
S3_BUCKET = "your-textract-bucket"
REGION = "us-east-1"

textract = boto3.client("textract", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)

# Example local reference data to compare
reference_totals = {"invoice1.pdf": 499.0, "invoice2.pdf": 320.5}

# -------------------------------
# FUNCTION: Upload file to S3
# -------------------------------
def upload_to_s3(file_path, bucket, key):
    s3.upload_file(file_path, bucket, key)
    print(f"Uploaded {file_path} to s3://{bucket}/{key}")

# -------------------------------
# FUNCTION: Start Textract job
# -------------------------------
def start_textract(bucket, document):
    response = textract.start_document_text_detection(
        DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': document}}
    )
    return response["JobId"]

# -------------------------------
# FUNCTION: Wait for job to complete
# -------------------------------
def wait_for_job(job_id):
    while True:
        result = textract.get_document_text_detection(JobId=job_id)
        status = result["JobStatus"]
        if status in ["SUCCEEDED", "FAILED"]:
            break
        time.sleep(5)
    if status != "SUCCEEDED":
        raise Exception("Textract job failed")
    return result

# -------------------------------
# FUNCTION: Extract lines from Textract result
# -------------------------------
def get_lines(textract_result):
    lines = [block["Text"] for block in textract_result["Blocks"] if block["BlockType"] == "LINE"]
    return lines

# -------------------------------
# FUNCTION: Extract total number from text
# -------------------------------
def extract_total(lines):
    for line in lines:
        match = re.search(r"\d+(\.\d+)?", line)
        if match:
            return float(match.group(0))
    return None

# -------------------------------
# MAIN AUTOMATION LOOP
# -------------------------------
for filename in os.listdir(LOCAL_FOLDER):
    if filename.lower().endswith(".pdf"):
        local_path = os.path.join(LOCAL_FOLDER, filename)
        s3_key = filename

        # 1️⃣ Upload to S3
        upload_to_s3(local_path, S3_BUCKET, s3_key)

        # 2️⃣ Start Textract job
        job_id = start_textract(S3_BUCKET, s3_key)
        print(f"Started Textract job for {filename}, Job ID: {job_id}")

        # 3️⃣ Wait for completion
        result = wait_for_job(job_id)
        print(f"Textract job completed for {filename}")

        # 4️⃣ Extract lines
        lines = get_lines(result)

        # 5️⃣ Extract total number (example)
        total = extract_total(lines)
        print(f"Extracted total: {total}")

        # 6️⃣ Compare with local reference data
        ref_total = reference_totals.get(filename)
        if ref_total is not None:
            if total == ref_total:
                print(f"✅ Total matches reference: {total}")
            else:
                print(f"❌ Total mismatch! Extracted: {total}, Reference: {ref_total}")
        print("==============================\n")
