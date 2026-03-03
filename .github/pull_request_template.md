## 📝 Description
Briefly describe the changes in this PR.

## 🎯 Type of Change
- [ ] 🐛 Bug fix (non-breaking change fixing an issue)
- [ ] ✨ New feature (non-breaking change adding functionality)
- [ ] 🚀 New skill implementation
- [ ] 📚 Documentation update
- [ ] 🧹 Refactoring (no functional changes)
- [ ] ⚙️ Infrastructure / CI / build improvements
- [ ] 🔐 Security improvement

## 🔗 Related Issues
Closes #(issue number) or relates to #(issue number)

## ✅ Checklist

### Code Quality
- [ ] Code follows project style guidelines (cargo fmt, ruff)
- [ ] cargo clippy passes with no warnings
- [ ] No commented-out code left behind
- [ ] New functions have clear, descriptive names

### Tests & Verification
- [ ] Changes have been tested locally
- [ ] New tests added for new functionality (if applicable)
- [ ] All tests pass (`cargo test --workspace`)
- [ ] No regressions in existing functionality

### Documentation
- [ ] README updated (if user-facing changes)
- [ ] Code comments added for complex logic
- [ ] Commit messages are clear and descriptive
- [ ] CHANGELOG.md updated (if user-facing changes)

### Security
- [ ] No hardcoded secrets or credentials
- [ ] New permissions are clearly documented
- [ ] Input validation is present where needed
- [ ] No command injection or unsafe SQL patterns (for skills)

### Skill-Specific (if applicable)
- [ ] `skillguard.yaml` manifest is complete and accurate
- [ ] `skill.py` implements error handling and dry-run support
- [ ] `__init__.py` exports `create_skill` factory function
- [ ] New permissions are justified and minimal
- [ ] Sandbox boundary checks are in place (path traversal, etc.)

## 🚀 Deployment Notes
Any special considerations for deploying or using this change?

## 📸 Screenshots (if applicable)
Add screenshots for UI changes, new documentation, or visual improvements.

## 🙏 Thanks
Thanks for contributing to SkillGuard! Please let us know if you have any questions.
