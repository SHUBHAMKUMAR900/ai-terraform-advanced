import os
from jinja2 import Environment, FileSystemLoader

def render_template(template_path, variables, output_path):
    # Load templates from the 'templates' directory
    env = Environment(loader=FileSystemLoader("templates"))

    # Load the specific file (just filename, not full path)
    template_file = os.path.basename(template_path)
    template = env.get_template(template_file)

    # Render the file with the provided variables
    rendered = template.render(variables)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write the rendered content to the output Terraform file
    with open(output_path, "w") as f:
        f.write(rendered)

    print(f"✅ Rendered Terraform file saved to: {output_path}")
