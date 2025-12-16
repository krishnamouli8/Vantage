# Secrets Management Guide for Vantage Platform

## Overview

This document provides guidance on securely managing secrets and sensitive configuration for the Vantage Observability Platform in production environments.

## ⚠️ Critical Security Warning

**DO NOT use `.env` files or environment variables for secrets in production!**

Environment variables and `.env` files are:

- ❌ Often committed to version control by mistake
- ❌ Visible in process listings (`ps aux`)
- ❌ Logged in application startup logs
- ❌ Accessible to all processes on the same machine
- ❌ Difficult to rotate without downtime

## Recommended Solutions

### 1. AWS Secrets Manager (AWS)

**Best for**: AWS deployments

```python
# Install SDK
pip install boto3

# Retrieve secrets in code
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name='us-east-1'
    )

    try:
        response = client.get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except ClientError as e:
        raise Exception(f"Error retrieving secret: {e}")

# Usage
api_key = get_secret('vantage/api-key')
clickhouse_password = get_secret('vantage/clickhouse-password')
```

**Configuration**:

```bash
# Store secrets
aws secretsmanager create-secret \
    --name vantage/api-key \
    --secret-string "your-secret-api-key"

# Grant IAM permissions to EC2/ECS
{
  "Effect": "Allow",
  "Action": [
    "secretsmanager:GetSecretValue"
  ],
  "Resource": "arn:aws:secretsmanager:*:*:secret:vantage/*"
}
```

---

### 2. HashiCorp Vault

**Best for**: Multi-cloud or on-premises

```python
# Install client
pip install hvac

# Retrieve secrets
import hvac

client = hvac.Client(url='https://vault.example.com:8200')
client.auth.approle.login(
    role_id='your-role-id',
    secret_id='your-secret-id'
)

secret = client.secrets.kv.v2.read_secret_version(
    path='vantage/config'
)

api_key = secret['data']['data']['api_key']
```

**Configuration**:

```bash
# Enable KV secrets engine
vault secrets enable -version=2 kv

# Store secrets
vault kv put kv/vantage/config \
    api_key="your-api-key" \
    clickhouse_password="your-password"

# Create policy
vault policy write vantage-read - <<EOF
path "kv/data/vantage/*" {
  capabilities = ["read"]
}
EOF

# Create AppRole
vault auth enable approle
vault write auth/approle/role/vantage-collector \
    token_policies="vantage-read" \
    token_ttl=1h \
    token_max_ttl=4h
```

---

### 3. Kubernetes Secrets

**Best for**: Kubernetes deployments

```yaml
# Create secret
apiVersion: v1
kind: Secret
metadata:
  name: vantage-secrets
type: Opaque
stringData:
  api-key: "your-secret-api-key"
  clickhouse-password: "your-password"
```

**Mount in deployment**:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vantage-collector
spec:
  template:
    spec:
      containers:
        - name: collector
          image: vantage-collector:latest
          env:
            - name: VANTAGE_API_KEY
              valueFrom:
                secretKeyRef:
                  name: vantage-secrets
                  key: api-key
            - name: WORKER_CLICKHOUSE_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: vantage-secrets
                  key: clickhouse-password
```

**Best practices**:

- Use **sealed-secrets** or **external-secrets** for GitOps
- Enable **encryption at rest** for etcd
- Use **RBAC** to limit secret access

---

### 4. Azure Key Vault

**Best for**: Azure deployments

```python
# Install SDK
pip install azure-keyvault-secrets azure-identity

# Retrieve secrets
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(
    vault_url="https://your-vault.vault.azure.net/",
    credential=credential
)

api_key = client.get_secret("vantage-api-key").value
```

---

### 5. Google Cloud Secret Manager

**Best for**: GCP deployments

```python
# Install SDK
pip install google-cloud-secret-manager

# Retrieve secrets
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
name = f"projects/your-project/secrets/vantage-api-key/versions/latest"

response = client.access_secret_version(request={"name": name})
api_key = response.payload.data.decode('UTF-8')
```

---

## Secret Rotation Strategy

### 1. Zero-Downtime Rotation

```python
class SecretManager:
    def __init__(self):
        self.current_secret = None
        self.previous_secret = None
        self.refresh_interval = 300  # 5 minutes

    async def rotate_secret(self):
        """Rotate secret with grace period."""
        new_secret = await self.fetch_from_vault()

        # Keep previous secret valid for grace period
        self.previous_secret = self.current_secret
        self.current_secret = new_secret

        # Schedule cleanup of old secret
        asyncio.create_task(self.cleanup_old_secret())

    def validate_secret(self, provided_secret):
        """Validate against both current and previous secret."""
        return (
            provided_secret == self.current_secret or
            provided_secret == self.previous_secret
        )
```

### 2. Automated Rotation Schedule

```bash
# AWS Lambda for automated rotation (every 90 days)
aws secretsmanager rotate-secret \
    --secret-id vantage/api-key \
    --rotation-lambda-arn arn:aws:lambda:region:account:function:rotate-secret \
    --rotation-rules AutomaticallyAfterDays=90
```

---

## Migration from `.env` Files

### Step 1: Audit Current Secrets

```bash
# List all secrets in .env
grep -E "^[A-Z_]+=" .env | cut -d= -f1
```

### Step 2: Store in Secrets Manager

```bash
# For each secret
for secret in $(grep -E "^[A-Z_]+=" .env); do
    key=$(echo $secret | cut -d= -f1)
    value=$(echo $secret | cut -d= -f2)

    aws secretsmanager create-secret \
        --name "vantage/$key" \
        --secret-string "$value"
done
```

### Step 3: Update Application

```python
# Before (INSECURE)
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('VANTAGE_API_KEY')

# After (SECURE)
from secrets_manager import get_secret

api_key = get_secret('vantage/api-key')
```

### Step 4: Remove .env Files

```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo ".env.*" >> .gitignore

# Remove from repository history
git filter-branch --force --index-filter \
    'git rm --cached --ignore-unmatch .env' \
    --prune-empty --tag-name-filter cat -- --all
```

---

## Security Checklist

### Development

- [ ] Never commit `.env` files to version control
- [ ] Use `.env.example` with dummy values only
- [ ] Use separate secrets for dev/staging/production
- [ ] Document which secrets are required

### Production

- [ ] Use dedicated secrets management service
- [ ] Enable audit logging for secret access
- [ ] Implement secret rotation (90-day maximum)
- [ ] Use IAM roles/service accounts (no long-lived credentials)
- [ ] Encrypt secrets at rest and in transit
- [ ] Limit secret access with RBAC
- [ ] Monitor for secret leaks (tools like GitGuardian, TruffleHog)

### Vantage-Specific

- [ ] Rotate ClickHouse passwords every 90 days
- [ ] Rotate API keys when team members leave
- [ ] Use different API keys per environment
- [ ] Implement API key rate limiting
- [ ] Log API key usage for audit trail

---

## Secrets Required for Vantage

| Secret                       | Purpose                              | Rotation Frequency |
| ---------------------------- | ------------------------------------ | ------------------ |
| `VANTAGE_API_KEY`            | Collector authentication             | 90 days            |
| `API_KEY`                    | Query API authentication             | 90 days            |
| `WORKER_CLICKHOUSE_PASSWORD` | ClickHouse access                    | 90 days            |
| `API_CLICKHOUSE_PASSWORD`    | ClickHouse access                    | 90 days            |
| `KAFKA_SASL_PASSWORD`        | Kafka authentication (if using SASL) | 90 days            |

---

## Emergency Response

### If Secret is Leaked

1. **Immediately rotate** the compromised secret
2. **Revoke** the old secret
3. **Audit** access logs for unauthorized usage
4. **Notify** security team
5. **Update** all applications using new secret
6. **Document** incident for compliance

### Automated Leak Detection

```bash
# Scan git history for secrets
pip install truffleHog
truffleHog --regex --entropy=True .

# Scan codebase
pip install detect-secrets
detect-secrets scan > .secrets.baseline
```

---

## References

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [12-Factor App: Config](https://12factor.net/config)
- [AWS Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)
- [HashiCorp Vault Documentation](https://www.vaultproject.io/docs)
