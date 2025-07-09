import os
import json
import datetime
import subprocess
from dotenv import load_dotenv
import google.generativeai as genai

from render_template import render_template
from validate import validate_variables
from upload_to_s3 import upload_file_to_s3

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Resource templates and required variables
TEMPLATES = {
    "ec2": ("templates/ec2.tf.j2", ["region", "name", "ami", "instance_type"]),
    "vpc": ("templates/vpc.tf.j2", ["region", "name", "cidr_block"]),
    "s3": ("templates/s3.tf.j2", ["region", "name"]),
    "lambda": ("templates/lambda.tf.j2", ["region", "name", "runtime", "handler", "filename", "role_arn"]),
}


def get_ai_variables(prompt):
    """Ask Gemini to return only a valid JSON object with required Terraform keys."""
    model = genai.GenerativeModel(os.getenv("GEMINI_MODEL"))

    # Try to detect resource type and required keys
    resource_type = ""
    required_keys = []
    for key in TEMPLATES:
        if key in prompt.lower():
            resource_type = key
            required_keys = TEMPLATES[key][1]
            break

    instruction = (
        f"You are a Terraform assistant. Return only a VALID JSON object (no markdown) "
        f"with the following keys: {required_keys}. "
        f"Do NOT include explanations or code blocks. Prompt: {prompt}"
    )

    try:
        response = model.generate_content(instruction)
        content = response.text.strip()

        # Clean markdown if Gemini added ```json
        if content.startswith("```"):
            lines = content.splitlines()
            content = "\n".join(lines[1:-1]).strip()

        print("🧾 Cleaned Gemini response:\n", content)
        return json.loads(content)

    except json.JSONDecodeError:
        print("⚠️ Invalid JSON received. Gemini likely added extra text. Here's the raw:\n")
        print(content)
        return {}

    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        return {}


def run_terraform(output_file):
    """Runs terraform init and apply for the generated file"""
    terraform_dir = os.path.dirname(output_file)
    os.chdir(terraform_dir)

    print("\n🚀 Running terraform init...")
    subprocess.run(["terraform", "init"], check=True)

    print("🚀 Running terraform apply...")
    subprocess.run(["terraform", "apply", "-auto-approve"], check=True)


if __name__ == "__main__":
    # Step 1: Ask user for resource
    resource_type = input("🔧 Resource type (ec2, vpc, s3, lambda): ").strip().lower()
    if resource_type not in TEMPLATES:
        print("❌ Invalid resource type")
        exit()

    # Step 2: Ask user what they want
    prompt = input("💬 What do you want to create? (describe it): ")

    # Step 3: Ask Gemini to return variables
    variables = get_ai_variables(prompt)
    if not variables:
        print("❌ Could not retrieve valid variables from Gemini.")
        exit()

    print("✅ Variables from AI:", json.dumps(variables, indent=2))

    # Step 4: Validate variables
    template_path, required_keys = TEMPLATES[resource_type]
    if not validate_variables(variables, required_keys):
        print(f"❌ Missing required keys: {required_keys}")
        exit()

    # Step 5: Save variables locally
    with open("variables.json", "w") as f:
        json.dump(variables, f, indent=2)

    # Step 6: Generate Terraform file
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    output_file = f"terraform/{resource_type}-{timestamp}.tf"
    render_template(template_path, variables, output_file)

    print(f"✅ Terraform code generated at: {output_file}")

    # Step 7: Upload to S3
    upload_file_to_s3(output_file, os.getenv("S3_BUCKET_NAME"))
    print(f"📤 Uploaded to S3 bucket: {os.getenv('S3_BUCKET_NAME')}")

    # Step 8: Apply Terraform to create the real AWS resource
    run_terraform(output_file)
