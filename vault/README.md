
### Install Vault Server

```
helm install vault hashicorp/vault -n vault --create-namespace --values vault/vault-values.yaml
```

### Unseal Vault

```
kubectl exec vault-0 -- vault operator init \
    -key-shares=1 \
    -key-threshold=1 \
    -format=json > cluster-keys.json

cat cluster-keys.json  OR jq -r ".unseal_keys_b64[]" cluster-keys.json

VAULT_UNSEAL_KEY=$(jq -r ".unseal_keys_b64[]" cluster-keys.json)

kubectl exec vault-0 -- vault operator unseal $VAULT_UNSEAL_KEY
```

### Initial login to Vault
```
kubectl exec --stdin=true --tty=true vault-0 -n vault -- /bin/sh

vault login
```

### Vault UI

```
kubectl port-forward svc/vault 8200:8200 -n vault
```

### Create kubernetes authentication

```
vault auth enable -path kubernetes-auth kubernetes

vault write auth/kubernetes-auth/config kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
echo $KUBERNETES_PORT_443_TCP_ADDR
```


### Enable transit secrets engine

```
vault secrets enable -path=operator-transit transit

vault write -force operator-transit/keys/vso-client-cache


vault policy write auth-policy-operator - <<EOF
path "operator-transit/encrypt/vso-client-cache" {
   capabilities = ["create", "update"]
}
path "operator-transit/decrypt/vso-client-cache" {
   capabilities = ["create", "update"]
}
EOF


vault write auth/kubernetes-auth/role/auth-role-operator \
bound_service_account_names=vault-secrets-operator-controller-manager \
bound_service_account_namespaces=vault-secrets-operator-system \
token_ttl=0 \
token_period=120 \
token_policies=auth-policy-operator \
audience=vault
```

### Install Vault Secrets Operator

```
cat vault-secrets-operator-values.yaml

helm install vault-secrets-operator hashicorp/vault-secrets-operator -n vault-secrets-operator-system --create-namespace --values vault-secrets-operator-values.yaml
```

### Enable database secrets engine

```
vault secrets enable -path=micro-db database
```

### Create a rotating secret using the postgresql-database-plugin

```
vault write micro-db/config/micro-db \
plugin_name=postgresql-database-plugin \
allowed_roles="dev-postgres" \
connection_url="postgresql://{{username}}:{{password}}@DB_HOST_AND_PORT/microdb01?sslmode=require" \
username=<DB_USER> \
password=<DB_PASS>
```
### Create a role 

```
vault write micro-db/roles/dev-postgres \
db_name=micro-db \
creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
GRANT ALL PRIVILEGES ON DATABASE microdb01 TO \"{{name}}\"; \
GRANT USAGE ON SCHEMA public TO \"{{name}}\"; \
GRANT CREATE ON SCHEMA public TO \"{{name}}\"; \
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO \"{{name}}\"; \
GRANT ALL PRIVILEGES ON TABLE orders TO \"{{name}}\";" \
revocation_statements="REVOKE ALL ON DATABASE microdb01 FROM  \"{{name}}\";" \
backend=micro-db \
name=dev-postgres \
default_ttl="1m" \
max_ttl="1m"
```

### Credentials will be at the path micro-db/creds/dev-postgres

```
vault policy write auth-policy-db - <<EOF
path "micro-db/creds/dev-postgres" {
   capabilities = ["read"]
}
EOF
```

### Authorise a SA to access dev-postgres credetnials
```
vault write auth/kubernetes-auth/role/auth-role-db \
bound_service_account_names=dynamic-secret-db \
bound_service_account_namespaces=microservices-demo \
token_ttl=0 \
token_period=120 \
token_policies=auth-policy-db \
audience=vault
```

```
### Create transit engine service account
k apply -f dynamic-secrets/vault-operator-sa.yaml

### Create vaultauth to allow VSO use authenticattion config we just configure in vault
k apply -f dynamic-secrets/vault-auth-dynamic.yaml

### Create dynamnic secret
k apply -f dynamic-secrets/vault-dynamic-secret.yaml
```