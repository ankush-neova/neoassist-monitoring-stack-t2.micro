from zipfile import ZipFile
import os

# Define base path
base_dir = "/mnt/data/monitoring-stack-parameterized"

# Define parameter prompts
parameter_prompts = {
    "<REPLACE_DB_USER>": "Enter your PostgreSQL username",
    "<REPLACE_DB_PASSWORD>": "Enter your PostgreSQL password",
    "<REPLACE_DB_HOST>": "Enter your PostgreSQL host (IP or DNS)",
    "<REPLACE_DB_NAME>": "Enter your PostgreSQL database name",
    "<YOUR_JIRA_WEBHOOK_URL>": "Enter your Jira webhook URL"
}

# Placeholder values for demonstration (in real use, user would replace them)
example_values = {
    "<REPLACE_DB_USER>": "my_pg_user",
    "<REPLACE_DB_PASSWORD>": "my_pg_password",
    "<REPLACE_DB_HOST>": "mydb.example.com",
    "<REPLACE_DB_NAME>": "mydb",
    "<YOUR_JIRA_WEBHOOK_URL>": "https://jira.example.com/webhook"
}

# Define file templates with placeholders
files_to_create = {
    "docker-compose.yml": """version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./prometheus/targets/:/etc/prometheus/targets/
    command:
      - --config.file=/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter
    container_name: postgres-exporter
    environment:
      DATA_SOURCE_NAME: "postgresql://<REPLACE_DB_USER>:<REPLACE_DB_PASSWORD>@<REPLACE_DB_HOST>:5432/<REPLACE_DB_NAME>?sslmode=disable"
    ports:
      - "9187:9187"

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: cadvisor
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml

  jira-webhook:
    image: curlimages/curl
    container_name: jira-webhook
    entrypoint: ["/bin/sh", "-c"]
    command: ["while true; do sleep 3600; done"]
""",
    "prometheus/prometheus.yml": """global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'ec2-cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
""",
    "grafana/provisioning/datasources.yml": """apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
""",
    "grafana/provisioning/dashboards.yml": """apiVersion: 1

providers:
  - name: 'default'
    folder: ''
    type: file
    options:
      path: /var/lib/grafana/dashboards
""",
    "alertmanager/alertmanager.yml": """global:
  resolve_timeout: 5m

route:
  receiver: 'jira-webhook'

receivers:
  - name: 'jira-webhook'
    webhook_configs:
      - url: '<YOUR_JIRA_WEBHOOK_URL>'
""",
    "grafana/dashboards/PostgreSQL.json": "{}",
    "grafana/dashboards/Docker-ECR.json": "{}"
}

# Replace placeholders with example values
for path, content in files_to_create.items():
    for placeholder, example in example_values.items():
        content = content.replace(placeholder, example)
    file_path = os.path.join(base_dir, path)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        f.write(content)

# Create README for parameter guidance
readme_path = os.path.join(base_dir, "README.txt")
with open(readme_path, "w") as readme:
    readme.write("PARAMETERIZED MONITORING STACK SETUP\n")
    readme.write("====================================\n\n")
    readme.write("Before running the stack, please replace the following placeholders in the files:\n\n")
    for placeholder, prompt in parameter_prompts.items():
        readme.write(f"{placeholder}: {prompt}\n")

# Zip the folder
zip_path = "/mnt/data/monitoring-stack-parameterized.zip"
with ZipFile(zip_path, 'w') as zipf:
    for root, _, files in os.walk(base_dir):
        for file in files:
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, base_dir)
            zipf.write(abs_path, rel_path)

zip_path
