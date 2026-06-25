# Canonical entrypoint for lint/test/plan targets, modeled on pypi/infra.
#
# Each terraform/* leaf directory is a separate HCP Terraform workspace.
# Targets fan out across every leaf that has a versions.tf file.

TF_DIRS := $(shell find terraform -type f -name versions.tf -exec dirname {} \; | sort)

.PHONY: help fmt fmt-check validate init plan tf-dirs

help:
	@echo "Targets:"
	@echo "  fmt         - terraform fmt -recursive across terraform/"
	@echo "  fmt-check   - terraform fmt -check -recursive (CI gate)"
	@echo "  init        - terraform init in every workspace dir"
	@echo "  validate    - terraform validate in every workspace dir"
	@echo "  plan        - terraform plan in every workspace dir (requires HCP auth)"
	@echo "  tf-dirs     - list discovered workspace dirs"

tf-dirs:
	@printf '%s\n' $(TF_DIRS)

fmt:
	terraform fmt -recursive terraform/

fmt-check:
	terraform fmt -check -recursive terraform/

init:
	@for d in $(TF_DIRS); do \
		echo "==> init $$d"; \
		(cd $$d && terraform init -input=false) || exit $$?; \
	done

validate: init
	@for d in $(TF_DIRS); do \
		echo "==> validate $$d"; \
		(cd $$d && terraform validate) || exit $$?; \
	done

plan: init
	@for d in $(TF_DIRS); do \
		echo "==> plan $$d"; \
		(cd $$d && terraform plan -input=false) || exit $$?; \
	done
