# Terraform Patterns

Concrete DEV3 / DEV5 / DEV10 patterns specific to Terraform. For OpenTofu the same patterns apply (it's a Terraform fork at the time of writing). For Pulumi / CloudFormation / Ansible the DEV categories are the same; translate the syntax.

---

## DEV3 — IAC-IMMUTABILITY

### DEV3.1 — Drift between state and reality

**Antipatterns:**
- `terraform plan` shows pending changes for resources that were edited via the AWS / GCP / Azure console.
- New resource referenced by the code that is not yet in state (was created out-of-band).
- Tags reset by console edits and reasserted by `apply` — the human keeps fighting the IaC.

**Detection:** any PR that adds a new `resource "..."` block while the README or a runbook says "create the X first in the console, then `terraform apply`." That's the smell.

**Fix:** `terraform import` to bring console-created resources under management. The CI pipeline should run `terraform plan` on every PR and post the diff; PRs that show unexpected destroy/replace fail.

### DEV3.2 — State file leaked or local-only

**Antipatterns:**
- `terraform.tfstate` committed to git (cross-ref SEC7: state files contain unencrypted secrets).
- Backend block missing — state lives on the developer's laptop.
- S3 backend without DynamoDB lock table; two concurrent applies race.
- `terraform.tfstate.backup` committed.

**Fix:**

```hcl
terraform {
  backend "s3" {
    bucket         = "company-tfstate"
    key            = "services/api/prod.tfstate"
    region         = "us-east-1"
    dynamodb_table = "tfstate-lock"
    encrypt        = true
  }
}
```

For Terraform Cloud or HCP, the backend handles locking; verify the workspace exists.

### DEV3.3 — Provisioners mutating remote state

**Antipatterns:**
- `provisioner "local-exec"` running `aws s3 cp`, `kubectl apply`, or `gcloud sql instances patch` — turns the provider abstraction into shell scripts.
- `null_resource` with `triggers = { always = timestamp() }` — runs on every apply.
- `data "external"` shelling out to compute a value that should be a provider resource.

**Fix:** use the actual provider resource. AWS S3 object → `aws_s3_object`. k8s manifest → `kubernetes_manifest` (or the `helm` / `argocd` provider). DB patch → `google_sql_database_instance` updates.

### DEV3.4 — Renamed resource without `moved {}`

**Antipatterns:**

```hcl
# Before:
resource "aws_s3_bucket" "logs" { ... }

# After (without moved {}):
resource "aws_s3_bucket" "archived_logs" { ... }
```

`terraform plan` shows: destroy `aws_s3_bucket.logs`, create `aws_s3_bucket.archived_logs`. For a bucket with data, that's data loss.

**Fix:**

```hcl
resource "aws_s3_bucket" "archived_logs" { ... }

moved {
  from = aws_s3_bucket.logs
  to   = aws_s3_bucket.archived_logs
}
```

`terraform plan` becomes a no-op. Apply, then remove the `moved {}` block in a follow-up PR.

### DEV3.5 — Environment drift

**Antipatterns:**
- `dev/main.tf` and `prod/main.tf` have diverged: prod has resources dev lacks (and vice versa).
- Modules versioned by branch instead of tag in some envs.
- Variables defined in one env's `.tfvars` and not in another.

**Fix:** one module set, parameterized by `.tfvars`. Modules pinned to a tag:

```hcl
module "api" {
  source = "git::https://github.com/org/modules//api?ref=v2.4.0"
  ...
}
```

### DEV3.6 — Missing required_providers / required_version

**Antipatterns:**
- No `terraform { required_version = ... required_providers = ... }` block.
- Loose version constraints: `version = "> 4.0.0"`.

**Fix:**

```hcl
terraform {
  required_version = "~> 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.30.0"
    }
  }
}
```

---

## DEV5 — CONFIG-MGMT (Terraform framing)

### DEV5.1 — Secrets in `.tf` or `.tfvars`

**Antipatterns:**
- `variable "stripe_key" { default = "sk_live_..." }`.
- `prod.tfvars` committed with secrets baked in.
- Hardcoded ARNs / connection strings that are actually environment-specific values.

**Fix:** secrets from Secrets Manager / Parameter Store:

```hcl
data "aws_secretsmanager_secret_version" "stripe" {
  secret_id = "stripe-prod"
}

resource "aws_lambda_function" "checkout" {
  environment {
    variables = {
      STRIPE_KEY = data.aws_secretsmanager_secret_version.stripe.secret_string
    }
  }
}
```

For non-AWS, the equivalent: `google_secret_manager_secret_version`, `azurerm_key_vault_secret`, `vault_generic_secret`.

### DEV5.3 — Same module config across envs

`prod/main.tf` is a literal copy of `dev/main.tf` with the strings find-replaced. Inevitable drift.

**Fix:** environments call a shared module:

```hcl
# environments/prod/main.tf
module "api" {
  source       = "../../modules/api"
  environment  = "prod"
  instance_count = 6
  ...
}
```

---

## DEV10 — SLO-PERFORMANCE (Terraform framing)

### DEV10.1 — Compute without resource sizing

**Antipatterns:**
- `aws_ecs_task_definition` with no `cpu` / `memory` set (falls back to platform defaults, usually too low).
- `aws_lambda_function` with no `memory_size` / `timeout` set.
- `google_cloud_run_service` with no `resources` block.

**Fix:** explicit sizing; derive from observed usage; alert on hitting the limit.

### DEV10.2 — No autoscaling config on autoscale-eligible workload

`aws_ecs_service` with `desired_count = 2` and no `aws_appautoscaling_target` / `aws_appautoscaling_policy` — manual scaling only.

**Fix:** autoscaling target + policy + CloudWatch alarms feeding it.

---

## Terraform plan-gate pattern

A canonical CI flow that enforces the DEV3 rules:

```yaml
name: terraform
on: pull_request
permissions:
  contents: read
  id-token: write
  pull-requests: write
jobs:
  plan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<SHA> # v4.x
      - uses: aws-actions/configure-aws-credentials@<SHA>
        with:
          role-to-assume: arn:aws:iam::123:role/tf-plan-readonly
          aws-region: us-east-1
      - uses: hashicorp/setup-terraform@<SHA>
        with:
          terraform_version: 1.6.6
      - run: terraform init
      - run: terraform plan -out=tfplan -no-color | tee plan.txt
      - run: terraform show -no-color tfplan > plan-rendered.txt
      - uses: actions/upload-artifact@<SHA>
        with:
          name: tfplan
          path: |
            tfplan
            plan-rendered.txt
      # ... PR comment with plan diff
```

Apply happens on `main` push from a separate workflow that consumes the uploaded plan and runs `terraform apply tfplan`.

---

## File checklist

For Terraform changes, the skill verifies:

| Check | Antipattern | Pattern |
|-------|-------------|---------|
| Backend | No backend block / local state | Remote backend with locking |
| Versions | Loose / missing constraints | `required_version` + `required_providers` with `~>` |
| Renames | Plain rename | `moved {}` block |
| Secrets | Hardcoded in `.tf` / `.tfvars` | Pulled from secret manager via data source |
| Provisioners | `local-exec` mutating state | Provider resource |
| Plan gate | Apply on push with no plan review | `plan` artifact reviewed and consumed by `apply` |
| State | `.tfstate*` in git | Remote backend; `.gitignore` covers state |
| Env structure | Divergent per env | Shared module + per-env tfvars |
