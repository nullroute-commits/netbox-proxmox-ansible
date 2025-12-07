# Contributing to NetBox on Proxmox VE 9.1+

Thank you for your interest in contributing to this project! This document provides guidelines and instructions for contributing.

**System Information Collection:** Use [automation_nation.git](https://github.com/nullroute-commits/automation_nation.git) bash script to collect hardware and software information when reporting issues or testing changes.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Submitting Changes](#submitting-changes)
- [Style Guidelines](#style-guidelines)
- [Testing](#testing)

## Code of Conduct

This project adheres to a standard code of conduct. By participating, you are expected to uphold this code:

- **Be respectful** and inclusive of differing viewpoints
- **Be collaborative** and open to feedback
- **Be professional** in all interactions
- **Focus on what is best** for the community

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** (configuration files, commands, etc.)
- **Describe the behavior you observed** and what you expected
- **Include logs** from the deployment or service failures
- **Specify your environment:**
  - Proxmox VE version (9.0+, 9.1+ recommended)
  - Debian version
  - Ansible version
  - NetBox version
  - Hardware info (use automation_nation.git collect_info.sh)

**Bug Report Template:**
```markdown
**Description:**
Brief description of the issue

**Steps to Reproduce:**
1. Step one
2. Step two
3. Step three

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Environment:**
- Proxmox VE: 9.x (specify 9.0, 9.1, etc.)
- Debian: x.x
- Ansible: x.x
- NetBox: x.x
- Hardware: (attach automation_nation collect_info.sh output)

**Logs:**
```
Paste relevant logs here
```
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the suggested enhancement
- **Explain why this enhancement would be useful**
- **Provide examples** of how it would be used
- **Consider alternative solutions**

### Pull Requests

Pull requests are the best way to propose changes to the codebase:

1. **Fork the repository** and create your branch from `master`
2. **Make your changes** following the style guidelines
3. **Add or update tests** as appropriate
4. **Update documentation** if you're changing functionality
5. **Ensure all tests pass** before submitting
6. **Submit a pull request** with a clear description

**Pull Request Process:**

1. Update the README.md or relevant documentation with details of changes
2. Update the version numbers following [SemVer](https://semver.org/)
3. The PR will be merged once you have sign-off from maintainers

## Development Setup

### Prerequisites

```bash
# Install Ansible
apt install -y ansible

# Install required collections
ansible-galaxy collection install -r requirements.yml

# Clone the repository
git clone https://github.com/nullroute-commits/netbox-proxmox-ansible.git
cd netbox-proxmox-ansible
```

### Testing Your Changes

```bash
# Lint your playbooks
ansible-lint playbooks/*.yml

# Syntax check
ansible-playbook playbooks/site.yml --syntax-check

# Check in dry-run mode
ansible-playbook playbooks/site.yml --check

# Run verification
ansible-playbook playbooks/verify-deployment.yml
```

### Local Development Environment

For testing changes without affecting production:

1. **Use a test Proxmox environment**
2. **Create a separate branch** for your changes
3. **Test thoroughly** before submitting
4. **Document your changes** in commit messages

## Submitting Changes

### Commit Message Guidelines

Follow these guidelines for commit messages:

**Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting, missing semi-colons, etc.
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(nginx): Add Let's Encrypt support

- Add certbot role
- Configure automatic renewal
- Update nginx configuration template

Closes #123
```

```
fix(postgresql): Correct pg_hba.conf template

Fixed authentication issue for remote connections
by updating the subnet mask in pg_hba.conf template.

Fixes #456
```

### Branch Naming

Use descriptive branch names:
- `feature/add-letsencrypt`
- `bugfix/postgresql-connection`
- `docs/update-readme`
- `refactor/network-role`

## Style Guidelines

### Ansible Playbook Style

```yaml
---
# roles/example/tasks/main.yml

- name: Clear and descriptive task name
  module_name:
    parameter: value
    another_param: "{{ variable }}"
  register: result_variable
  when: condition
  tags: [tag1, tag2]

- name: Use proper YAML formatting
  module_name:
    param1: value1
    param2: value2
  become: yes
  notify: handler_name
```

**Best Practices:**
- Use descriptive task names
- One action per task
- Use `become: yes` explicitly when needed
- Register important results
- Use tags appropriately
- Keep lines under 120 characters
- Use quotes around variables in conditionals
- Indent consistently (2 spaces)

### Documentation Style

- Use Markdown for all documentation
- Include code examples where appropriate
- Keep explanations clear and concise
- Update TOC when adding sections
- Use proper heading hierarchy
- Include command outputs when helpful

### Variable Naming

```yaml
# Good
postgresql_max_connections: 100
netbox_admin_password: "{{ vault_netbox_admin_password }}"
backend_network_cidr: "10.100.0.0/24"

# Avoid
max_connections: 100
pwd: "secret"
net: "10.100.0.0/24"
```

**Conventions:**
- Use lowercase with underscores
- Prefix with role name for role variables
- Use descriptive names
- Store secrets in vault with `vault_` prefix

## Testing

### Unit Testing

Use Molecule for role testing:

```bash
cd roles/postgresql
molecule test
```

### Integration Testing

Test the complete deployment:

```bash
# Deploy to test environment
ansible-playbook playbooks/site.yml -i inventory/test

# Verify deployment
ansible-playbook playbooks/verify-deployment.yml
```

### Manual Testing Checklist

Before submitting a PR, verify:

- [ ] All containers start successfully
- [ ] All services are active
- [ ] Network connectivity between tiers works
- [ ] Database connections successful
- [ ] Web interface accessible
- [ ] No errors in logs
- [ ] Playbook is idempotent (can run multiple times)
- [ ] Documentation is updated
- [ ] Tests pass

## Project Structure

Understanding the project layout:

```
netbox-proxmox-ansible/
├── ansible.cfg           # Ansible configuration
├── requirements.yml      # Galaxy dependencies
├── inventory/           # Inventory files
├── group_vars/          # Global variables
├── playbooks/           # Playbooks
├── roles/               # Ansible roles
│   ├── role_name/
│   │   ├── tasks/       # Main tasks
│   │   ├── handlers/    # Handlers
│   │   ├── templates/   # Jinja2 templates
│   │   ├── files/       # Static files
│   │   ├── defaults/    # Default variables
│   │   └── meta/        # Role metadata
├── templates/           # Shared templates
├── files/              # Shared files
└── docs/               # Documentation
```

## Adding a New Role

To add a new role:

1. Create role structure:
```bash
mkdir -p roles/my_role/{tasks,handlers,templates,files,defaults,meta}
```

2. Create `tasks/main.yml`:
```yaml
---
- name: Task description
  module:
    param: value
```

3. Create `defaults/main.yml`:
```yaml
---
my_role_variable: default_value
```

4. Create `meta/main.yml`:
```yaml
---
dependencies: []
```

5. Add role to appropriate playbook

6. Document the role in README

## Documentation Requirements

When contributing, update:

- **README.md** - If adding new features
- **COMMAND_REFERENCE.md** - If adding new commands
- **ARCHITECTURE.md** - If changing architecture
- **ANSIBLE_DESIGN.md** - If modifying automation
- **Role README** - Document each role's purpose

## Questions?

If you have questions:

1. Check existing documentation in `docs/`
2. Search existing issues on GitHub
3. Create a new issue with the question label
4. Join community discussions

## Recognition

Contributors will be recognized in:
- GitHub contributors page
- Project documentation
- Release notes

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing!** Your efforts help make this project better for everyone.
