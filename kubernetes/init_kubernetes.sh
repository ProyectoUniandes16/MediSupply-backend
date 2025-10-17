#!/bin/bash

# Login to ECR
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID_JOSE.dkr.ecr.us-east-2.amazonaws.com

# Build and push images (amd64)
docker buildx build -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/auth-usuario:latest --push ./auth-usuario
docker buildx build -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/mediador-web:latest --push ./mediador-web
docker buildx build -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/producto-inventario-web:latest --push ./producto-inventario-web
docker buildx build -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/productos:latest --push ./productos_microservice
docker buildx build -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/vendedores:latest --push ./vendedores_microservice
docker buildx build -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/proveedores:latest --push ./proveedores_microservice

# Create EKS cluster
eksctl create cluster --name medisupply-cluster --region us-east-2 --nodes 5 --node-type t3.micro

# Configure kubectl
aws eks --region us-east-2 update-kubeconfig --name medisupply-cluster

# Deploy to Kubernetes
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f postgres-secret.yaml
kubectl apply -f postgres-deployment.yaml
kubectl apply -f postgres-service.yaml
kubectl apply -f auth-usuario/deployment.yaml
kubectl apply -f auth-usuario/service.yaml
kubectl apply -f mediador-web/deployment.yaml
kubectl apply -f mediador-web/service.yaml
kubectl apply -f producto-inventario-web/deployment.yaml
kubectl apply -f producto-inventario-web/service.yaml
kubectl apply -f productos/deployment.yaml
kubectl apply -f productos/service.yaml
kubectl apply -f proveedores/deployment.yaml
kubectl apply -f proveedores/service.yaml
kubectl apply -f vendedores/deployment.yaml
kubectl apply -f vendedores/service.yaml
kubectl apply -f ingress.yaml