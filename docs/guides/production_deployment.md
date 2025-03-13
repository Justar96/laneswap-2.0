# Deploying LaneSwap in Production

This guide provides instructions for deploying LaneSwap in a production environment. It covers best practices, security considerations, and different deployment options to help you set up a reliable and scalable LaneSwap system.

## Prerequisites

Before deploying LaneSwap in production, ensure you have:

- A thorough understanding of LaneSwap's architecture and components
- Experience with server administration and deployment
- Access to production-grade infrastructure (servers, databases, etc.)
- Familiarity with containerization and orchestration tools (Docker, Kubernetes, etc.)
- SSL certificates for secure communication

## Deployment Architecture

A typical production deployment of LaneSwap consists of the following components:

1. **LaneSwap API Server**: The central component that handles service registration, message routing, and API requests.
2. **Database**: Stores service information, message history, and other persistent data.
3. **Message Queue**: Handles asynchronous message processing and event distribution.
4. **Adapters**: Connect LaneSwap to external systems and services.
5. **Monitoring and Logging**: Track system health, performance, and issues.
6. **Load Balancer**: Distributes traffic across multiple API server instances for high availability.

## Deployment Options

### Option 1: Docker Compose

Docker Compose provides a simple way to deploy LaneSwap and its dependencies on a single server or a small cluster.

1. **Create a Docker Compose file**:

```yaml
version: '3.8'

services:
  laneswap-api:
    image: laneswap/api:latest
    restart: always
    ports:
      - "8000:8000"
    environment:
      - LANESWAP_CONFIG=/app/config/production.yaml
      - LANESWAP_DB_URI=postgresql://user:password@db:5432/laneswap
      - LANESWAP_REDIS_URI=redis://redis:6379/0
      - LANESWAP_LOG_LEVEL=INFO
    volumes:
      - ./config:/app/config
    depends_on:
      - db
      - redis
    networks:
      - laneswap-network

  db:
    image: postgres:13
    restart: always
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=laneswap
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - laneswap-network

  redis:
    image: redis:6
    restart: always
    volumes:
      - redis-data:/data
    networks:
      - laneswap-network

  adapter-example:
    image: laneswap/adapter-example:latest
    restart: always
    environment:
      - LANESWAP_API_URL=http://laneswap-api:8000
      - LANESWAP_API_KEY=your-api-key
    depends_on:
      - laneswap-api
    networks:
      - laneswap-network

networks:
  laneswap-network:

volumes:
  postgres-data:
  redis-data:
```

2. **Deploy with Docker Compose**:

```bash
docker-compose up -d
```

### Option 2: Kubernetes

For larger deployments with high availability requirements, Kubernetes is recommended.

1. **Create Kubernetes manifests**:

Create separate YAML files for each component (deployment, service, configmap, secret, etc.).

Example deployment for the API server:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: laneswap-api
  namespace: laneswap
spec:
  replicas: 3
  selector:
    matchLabels:
      app: laneswap-api
  template:
    metadata:
      labels:
        app: laneswap-api
    spec:
      containers:
      - name: laneswap-api
        image: laneswap/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: LANESWAP_CONFIG
          value: /app/config/production.yaml
        - name: LANESWAP_DB_URI
          valueFrom:
            secretKeyRef:
              name: laneswap-secrets
              key: db-uri
        - name: LANESWAP_REDIS_URI
          valueFrom:
            secretKeyRef:
              name: laneswap-secrets
              key: redis-uri
        - name: LANESWAP_LOG_LEVEL
          value: INFO
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config-volume
        configMap:
          name: laneswap-config
```

2. **Deploy to Kubernetes**:

```bash
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/secrets.yaml
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/database.yaml
kubectl apply -f kubernetes/redis.yaml
kubectl apply -f kubernetes/api.yaml
kubectl apply -f kubernetes/adapters.yaml
kubectl apply -f kubernetes/ingress.yaml
```

### Option 3: Serverless Deployment

For certain components, a serverless deployment can be cost-effective and scalable.

Example AWS Lambda function for an adapter:

```python
import json
import os
from laneswap.client import LaneSwapClient
from laneswap.core.models import ServiceType

client = LaneSwapClient(
    api_url=os.environ["LANESWAP_API_URL"],
    api_key=os.environ["LANESWAP_API_KEY"],
    service_name="lambda-adapter",
    service_type=ServiceType.ADAPTER
)

def lambda_handler(event, context):
    # Process the event
    message = {
        "source": "aws-lambda",
        "content": event
    }
    
    # Send the message to LaneSwap
    response = client.send_message_sync("target-service-id", message)
    
    return {
        "statusCode": 200,
        "body": json.dumps(response)
    }
```

## Configuration for Production

Create a production configuration file with appropriate settings:

```yaml
# production.yaml
api:
  host: 0.0.0.0
  port: 8000
  workers: 4
  timeout: 60
  cors_origins:
    - https://yourdomain.com
  rate_limit:
    enabled: true
    requests_per_minute: 100

database:
  uri: ${LANESWAP_DB_URI}
  pool_size: 20
  max_overflow: 10
  pool_timeout: 30

redis:
  uri: ${LANESWAP_REDIS_URI}
  pool_size: 10

security:
  api_keys:
    enabled: true
    key_rotation_days: 90
  jwt:
    secret: ${LANESWAP_JWT_SECRET}
    algorithm: HS256
    expiration_minutes: 60
  ssl:
    enabled: true
    cert_file: /path/to/cert.pem
    key_file: /path/to/key.pem

logging:
  level: ${LANESWAP_LOG_LEVEL}
  format: json
  output:
    console: true
    file:
      enabled: true
      path: /var/log/laneswap/api.log
      max_size_mb: 100
      backup_count: 10

services:
  heartbeat:
    interval_seconds: 30
    timeout_seconds: 90
  cleanup:
    enabled: true
    interval_hours: 24
    message_retention_days: 30
```

## Security Considerations

1. **API Authentication**:
   - Use API keys for service-to-service communication
   - Implement JWT for user authentication
   - Rotate credentials regularly

2. **Network Security**:
   - Use HTTPS for all external communication
   - Set up a firewall to restrict access to the API server
   - Use a VPN or private network for internal communication

3. **Data Protection**:
   - Encrypt sensitive data at rest and in transit
   - Implement proper access controls for the database
   - Regularly backup data and test restoration procedures

4. **Monitoring and Alerting**:
   - Set up monitoring for system health and performance
   - Configure alerts for critical issues
   - Implement logging for auditing and troubleshooting

## Scaling Considerations

1. **Horizontal Scaling**:
   - Deploy multiple instances of the API server behind a load balancer
   - Use a distributed database for high availability
   - Implement caching for frequently accessed data

2. **Vertical Scaling**:
   - Allocate sufficient resources (CPU, memory) for each component
   - Monitor resource usage and adjust as needed
   - Use appropriate instance types for different workloads

3. **Database Scaling**:
   - Implement read replicas for read-heavy workloads
   - Consider sharding for large datasets
   - Use connection pooling to manage database connections

## Monitoring and Logging

1. **Monitoring Tools**:
   - Prometheus for metrics collection
   - Grafana for visualization
   - Alertmanager for alerting

2. **Logging Setup**:
   - ELK Stack (Elasticsearch, Logstash, Kibana) for log aggregation
   - Structured logging in JSON format
   - Log rotation to manage disk space

3. **Health Checks**:
   - Implement health check endpoints for each component
   - Configure liveness and readiness probes for Kubernetes
   - Set up uptime monitoring with tools like Pingdom or UptimeRobot

## Backup and Disaster Recovery

1. **Database Backups**:
   - Schedule regular backups of the database
   - Store backups in a secure, off-site location
   - Test restoration procedures regularly

2. **Configuration Backups**:
   - Version control your configuration files
   - Use infrastructure as code (IaC) tools like Terraform
   - Document deployment procedures

3. **Disaster Recovery Plan**:
   - Define recovery point objective (RPO) and recovery time objective (RTO)
   - Create a step-by-step recovery procedure
   - Conduct regular disaster recovery drills

## Continuous Integration and Deployment

1. **CI/CD Pipeline**:
   - Automate testing and deployment
   - Use a blue-green deployment strategy
   - Implement canary releases for high-risk changes

2. **Versioning**:
   - Use semantic versioning for releases
   - Tag Docker images with specific versions
   - Maintain a changelog

3. **Rollback Procedures**:
   - Define clear rollback procedures
   - Test rollback capabilities
   - Monitor deployments for issues

## Production Checklist

Before going live, ensure you have:

- [ ] Completed thorough testing in a staging environment
- [ ] Set up monitoring and alerting
- [ ] Implemented backup and disaster recovery procedures
- [ ] Documented deployment and operational procedures
- [ ] Trained operations staff
- [ ] Conducted a security review
- [ ] Established an incident response plan
- [ ] Set up a logging and auditing system
- [ ] Configured appropriate resource limits
- [ ] Tested scaling capabilities

## Conclusion

Deploying LaneSwap in production requires careful planning and consideration of various factors such as security, scalability, and reliability. By following the guidelines in this document, you can set up a robust and efficient LaneSwap system that meets your production requirements.

For additional support or questions, refer to the [LaneSwap documentation](https://laneswap.readthedocs.io/) or contact the LaneSwap team. 