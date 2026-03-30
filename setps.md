give a diagram about how this flow works


use vairables and explain those variables using <VARIABLE> for everything to make it generic

Mention that now we are running the keycloak on ec2 but for production we should run it on eks or some cluster or atleast use asg and load balancer

explain about getting the certificate using ngix and certbot and also about a domain need to be registered in the route 53 and what record to add there, etc
And mention that for production, we need to get acm certificate

### 1. Install Keycloak on EC2

```bash
sudo apt update -y && sudo apt install -y docker.io nginx certbot python3-certbot-nginx
sudo systemctl start docker && sudo systemctl enable docker

sudo docker run -d \
  --name keycloak \
  --restart always \
  -p 8080:8080 \
  -v keycloak_data:/opt/keycloak/data \
  --security-opt seccomp=unconfined \
  -e KC_BOOTSTRAP_ADMIN_USERNAME=admin \
  -e KC_BOOTSTRAP_ADMIN_PASSWORD=admin \
  -e KC_HOSTNAME=https://keycloak.modernops.in \
  -e KC_HOSTNAME_STRICT=false \
  -e KC_HTTP_ENABLED=true \
  -e KC_PROXY_HEADERS=xforwarded \
  -e KC_DB=dev-file \
  quay.io/keycloak/keycloak:latest \
  start-dev
```
explain about the steps here and also suggest the production way of deploying it
like usin postgres or if it is cluster we can use...



go to https://keycloak.modernops.in and login using username and password

---

### 2. Create Realm
- Name: `agentcore-mcp`

use realm
---

### 3. Create Client
- Client ID: `agentcore-mcp-client`
- Client authentication: **ON**
- Direct access grants: **ON**
- Standard flow: **ON**
- Valid redirect URIs:
  ```
  https://studio.presidio.ai/api/v1/connectors/oauth/callback
  https://studio.presidio.ai/auth/v1/callback
  ```
- Post logout redirect URI: `https://studio.presidio.ai`
- Web origins: `https://studio.presidio.ai`

---

### 4. Add Hardcoded client_id Mapper

**Clients → agentcore-mcp-client → Client Scopes → agentcore-mcp-client-dedicated → Mappers → Add mapper → By configuration → Hardcoded claim**

| Field | Value |
|---|---|
| Name | `client_id` |
| Token claim name | `client_id` |
| Claim value | `agentcore-mcp-client` |
| Claim JSON type | `String` |
| Add to access token | **ON** |

---

### 5. Create User
- Users → Create new user
- Set username, email, email verified **ON**
- Credentials → Set password → Temporary **OFF**

---
6. Configure Inbound Auth on the AgentCore Runtime
After creating the AgentCore MCP runtime, configure OAuth inbound authentication so that the runtime can validate requests using tokens issued by Amazon Cognito. This configuration enables the MCP endpoint to accept Bearer tokens generated from the Cognito User Pool and ensures that only authenticated clients can invoke the runtime.

Using the AWS Console
Navigate to Amazon Bedrock → AgentCore Runtime.

Select the runtime created in the previous step.

Choose Update hosting configuration.

Locate the Inbound Authentication section.

Configure the Discovery URL to:

The discovery endpoint allows AgentCore to automatically retrieve below. This enables the runtime to validate JWT access tokens issued by keycloak

Token validation endpoints

Public signing keys

OAuth configuration details



https://DOMAIN/realms/REALM/.well-known/openid-configuration
Example: https://keycloak.modernops.in/realms/agentcore-mcp/.well-known/openid-configuration
Configure the client ID of Cognito keycloack Client created earlier. Once the configuration is complete, the AgentCore runtime will begin validating incoming requests using keycloak-issued Bearer tokens. Below snippet is the reference of it.



Generate the AgentCore Endpoint URL
The endpoint URL is how the MCP client connects to deployed server, requiring proper URL encoding of the runtime ARN. The endpoint URL is required to connect AI Studio to the AgentCore MCP runtime.

Get the Runtime ARN


export RUNTIME_ARN=$(aws bedrock-agentcore-control get-agent-runtime \
  --agent-runtime-id <AGENT_RUNTIME_ID> \
  --region us-east-1 \
  | jq -r '.agentRuntimeArn')
ARN Encoding

Encoding is required because the AgentCore runtime API communicates using JSON over HTTP, which only supports text data. When MCP tools exchange binary or complex data, it must be encoded (Commonly using Base64) to ensure safe and reliable transmission. The runtime then decodes the payload before processing it, preventing data corruption during transport. 

Quick encoding with sed:

The ARN must have : replaced with %3A and / replaced with %2F.

Example:

RUNTIME_ARN : arn:aws:bedrock-agentcore:us-east-1:542115676974:runtime/aws-api-mcp-server

Encoded:  arn%3Aaws%3Abedrock-agentcore%3Aus-east-1%3A542115676974%3Aruntime%2Faws-api-mcp-server

Get the endpoint using this command



export ENDPOINT_URL="https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/$(echo $RUNTIME_ARN | sed 's/:/%3A/g; s/\//%2F/g')/invocations?qualifier=DEFAULT"
echo "Endpoint URL: $ENDPOINT_URL"
Full endpoint URL example:



https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn%3Aaws%3Abedrock-agentcore%3Aus-east-1%3A542115676974%3Aruntime%2Fawsapimcpserveroauth-CkhcIJA7qI/invocations?qualifier=endpoint_rquh6


Connect to AI Studio
Create MCP Connector

Navigate to AI Studio → MCP Connectors → Create New Connector.

Provide a Name and Description for the connector.

The description helps the agent determine when to invoke this MCP server, so make it clear and specific ( For example: “Provides access to AWS APIs via MCP. Use for AWS resource management tasks.”).

Set the Base URL to the endpoint URL generated in Step 10.

Create an Authentication Provider

Under the connector, create a new auth provider with below details:

Field

Value

Authentication Type

OAuth 2.0

Client ID

<CLIENT_ID from Step 2>

Client Secret

<CLIENT_SECRET from Step 2>

Issuer URL

https://cognito-idp.us-east-1.amazonaws.com/<USER_POOL_ID>

Scope

openid





### 7. AI Studio credentials

| Field | Value |
|---|---|
| **Issuer URL** | `https://keycloak.modernops.in/realms/agentcore-mcp` |
| **Discovery URL** | `https://keycloak.modernops.in/realms/agentcore-mcp/.well-known/openid-configuration` |
| **Token URL** | `https://keycloak.modernops.in/realms/agentcore-mcp/protocol/openid-connect/token` |
| **Client ID** | `agentcore-mcp-client` |
| **Client Secret** | from Credentials tab |
| **Scope** | `openid` |




Create a complete doc for this in md, replace cognito with keycloak 
Leave space for screenshots
