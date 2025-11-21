#!/bin/bash

# Login to ECR
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 012146976167.dkr.ecr.us-east-2.amazonaws.com

# Build and push images (arm64)
docker buildx build --no-cache --platform linux/amd64 -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/auth-usuario:latest --push ./auth-usuario
docker buildx build --no-cache --platform linux/amd64 -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/mediador-web:latest --push ./mediador-web
docker buildx build --no-cache --platform linux/amd64 -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/producto-inventario-web:latest --push ./producto-inventario-web
docker buildx build --no-cache --platform linux/amd64 -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/productos:latest --push ./productos_microservice
docker buildx build --no-cache --platform linux/amd64 -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/vendedores:latest --push ./vendedores_microservice
docker buildx build --no-cache --platform linux/amd64 -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/proveedores:latest --push ./proveedores_microservice
docker buildx build --no-cache --platform linux/amd64 -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/clientes:latest --push ./clientes_microservice
docker buildx build --no-cache --platform linux/amd64 -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/mediador-movil:latest --push ./mediador-movil
docker buildx build --no-cache --platform linux/amd64 -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/redis-service:latest --push ./redis_service
docker buildx build --no-cache --platform linux/amd64 -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/producto-inventario-movil:latest --push ./producto-inventario-movil
docker buildx build --no-cache --platform linux/amd64 -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/pedidos:latest --push ./pedidos_microservice
docker buildx build --no-cache --platform linux/amd64 -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/inventarios:latest --push ./inventarios_microservice
docker buildx build --no-cache --platform linux/amd64 -t 012146976167.dkr.ecr.us-east-2.amazonaws.com/logistica:latest --push ./logistica_microservice


# Create EKS cluster
eksctl create cluster --name medisupply-cluster --region us-east-2 --nodes 15 --node-type t3.micro

# Configure kubectl
aws eks --region us-east-2 update-kubeconfig --name medisupply-cluster

# Deploy to Kubernetes
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/postgres-secret.yaml
kubectl apply -f kubernetes/postgres-deployment.yaml
kubectl apply -f kubernetes/redis-deployment.yaml
kubectl apply -f kubernetes/redis-service.yaml
kubectl apply -f kubernetes/postgres-service.yaml
kubectl apply -f kubernetes/auth-usuario/deployment.yaml
kubectl apply -f kubernetes/auth-usuario/service.yaml
kubectl apply -f kubernetes/mediador-web/deployment.yaml
kubectl apply -f kubernetes/mediador-web/service.yaml
kubectl apply -f kubernetes/producto-inventario-web/deployment.yaml
kubectl apply -f kubernetes/producto-inventario-web/service.yaml
kubectl apply -f kubernetes/mediador-movil/deployment.yaml
kubectl apply -f kubernetes/mediador-movil/service.yaml
kubectl apply -f kubernetes/producto-inventario-movil/deployment.yaml
kubectl apply -f kubernetes/producto-inventario-movil/service.yaml
kubectl apply -f kubernetes/productos/deployment.yaml
kubectl apply -f kubernetes/productos/service.yaml
kubectl apply -f kubernetes/inventarios/deployment.yaml
kubectl apply -f kubernetes/inventarios/service.yaml
kubectl apply -f kubernetes/proveedores/deployment.yaml
kubectl apply -f kubernetes/proveedores/service.yaml
kubectl apply -f kubernetes/vendedores/deployment.yaml
kubectl apply -f kubernetes/vendedores/service.yaml
kubectl apply -f kubernetes/pedidos/deployment.yaml
kubectl apply -f kubernetes/pedidos/service.yaml
kubectl apply -f kubernetes/clientes/deployment.yaml
kubectl apply -f kubernetes/clientes/service.yaml
kubectl apply -f kubernetes/logistica/deployment.yaml
kubectl apply -f kubernetes/logistica/service.yaml
kubectl apply -f kubernetes/ingress.yaml

# Agrega el repo de ingress-nginx
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Instala el controlador en el namespace kube-system (o crea uno dedicado)
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace kube-system \
  --set controller.publishService.enabled=true

  kubectl get svc -n kube-system | grep nginx-ingress