


# Kafka Consumer Application Deployment

This Docs contains the Kafka Consumer application and provides a complete example guide to deploying it in production using Docker, CI/CD, Terraform, and Kubernetes.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [CI/CD Pipeline](#cicd-pipeline)
3. [Infrastructure Provisioning with Terraform](#infrastructure-provisioning-with-terraform)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [CI/CD Pipeline Example](#cicd-pipeline-example)
6. [Observability](#observability)
7. [Scaling and Optimization](#scaling-and-optimization)

---

## Prerequisites
1. **Source Control**: Git (e.g., GitHub, GitLab, Bitbucket).
2. **Container Registry**: Docker Hub, AWS ECR, or Azure ACR.
3. **CI/CD Tool**: GitHub Actions, GitLab CI, or Jenkins.
4. **Infrastructure as Code Tool**: Terraform for Kubernetes provisioning.
5. **Kubernetes Cluster**: Managed services like AWS EKS, Azure AKS, or GCP GKE.
6. **Helm (Optional)**: For simplified Kubernetes deployment.

---

## CI/CD Pipeline

### CI Steps
1. **Build Docker Image**:
   - Build the application’s Docker image and push it to the container registry.
2. **Run Unit Tests**:
   - Use Poetry to install dependencies and run tests.
3. **Lint and Format**:
   - Use tools like `flake8` and `black` for code quality checks.

### CD Steps
1. **Provision Infrastructure**:
   - Use Terraform to provision Kubernetes clusters and resources.
2. **Deploy to Kubernetes**:
   - Use `kubectl` or Helm to deploy manifests or Helm charts.

---
```
## Infrastructure Provisioning with Terraform

### Example `main.tf` for AWS EKS
``` hcl
provider "aws" {
  region = "us-east-1"
}

module "eks" {
  source          = "terraform-aws-modules/eks/aws"
  cluster_name    = "my-k8s-cluster"
  cluster_version = "1.25"
  subnets         = ["subnet-12345678", "subnet-87654321"]
  vpc_id          = "vpc-12345678"
  node_groups = {
    default = {
      desired_capacity = 2
      max_capacity     = 3
      min_capacity     = 1
    }
  }
}

We need add more here (this is just an example)
```

#### Commands to Run Terraform:
```bash
terraform init
terraform plan
terraform apply
```

---

## Kubernetes Deployment

### Example `deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kafka-consumer
  labels:
    app: kafka-consumer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: kafka-consumer
  template:
    metadata:
      labels:
        app: kafka-consumer
    spec:
      containers:
      - name: kafka-consumer
        image: <container-registry>/kafka-consumer:latest
        ports:
        - containerPort: 8080
        env:
        - name: KAFKA_BROKER_URL
          value: "kafka-broker:9092"
        - name: KAFKA_TOPIC
          value: "processed-user-events"
        - name: PYTHON_ENV
          value: "production"
```

### Example `service.yaml`
```yaml
apiVersion: v1
kind: Service
metadata:
  name: kafka-consumer-service
spec:
  selector:
    app: kafka-consumer
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
  type: ClusterIP
```

#### Deployment Commands
```bash
kubectl apply -f deployment.yaml -f service.yaml
```

---

## CI/CD Pipeline Example

### Example GitHub Actions Workflow (`.github/workflows/ci-cd.yml`)
```yaml
name: CI/CD Pipeline

on:
  push:
    branches:
      - main

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.9

      - name: Install Poetry
        run: python3 -m pip install poetry

      - name: Install Dependencies
        run: poetry install

      - name: Run Unit Tests
        run: poetry run python3 -m coverage run -m unittest discover

      - name: Build Docker Image
        run: |
          docker build -t <container-registry>/kafka-consumer:${{ github.sha }} .
          docker push <container-registry>/kafka-consumer:${{ github.sha }}

  deploy:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Checkout Code
        uses: actions/checkout@v3

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v3
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Setup Kubectl
        uses: azure/setup-kubectl@v3
        with:
          version: 'v1.25.0'

      - name: Authenticate with AWS EKS
        run: |
          aws eks update-kubeconfig --region us-east-1 --name my-cluster

      - name: Deploy to Kubernetes
        run: |
          kubectl apply -f deployment.yaml
          kubectl apply -f service.yaml

```

---

## Observability

- **Monitoring**: Use Prometheus and Grafana to monitor application metrics.
- **Logging**: Use Fluentd, Elasticsearch, and Kibana for log aggregation and analysis.

---

## Scaling and Optimization

- **Autoscaling**: Configure Horizontal Pod Autoscaler (HPA) for scaling based on CPU/memory usage.
- **Secrets Management**: Use Kubernetes Secrets or HashiCorp Vault for secure secrets management.

---

## License
This project is licensed under the [MIT License](LICENSE).

---

