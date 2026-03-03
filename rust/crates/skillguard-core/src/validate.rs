use crate::error::{Result, SkillGuardError};
use crate::manifest::SkillManifest;
use regex::Regex;
use std::sync::LazyLock;

static SKILL_NAME_RE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^[a-z][a-z0-9-]*[a-z0-9]$").unwrap());

/// A validated skill name.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct SkillName(String);

impl SkillName {
    pub fn new(name: &str) -> Result<Self> {
        if name.len() < 2 {
            return Err(SkillGuardError::InvalidSkillName {
                name: name.to_string(),
                reason: "Name must be at least 2 characters".into(),
            });
        }
        if name.len() > 64 {
            return Err(SkillGuardError::InvalidSkillName {
                name: name.to_string(),
                reason: "Name must be at most 64 characters".into(),
            });
        }
        if !SKILL_NAME_RE.is_match(name) {
            return Err(SkillGuardError::InvalidSkillName {
                name: name.to_string(),
                reason: "Must start with a letter, contain only lowercase letters, digits, and hyphens, and end with a letter or digit".into(),
            });
        }
        Ok(Self(name.to_string()))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl std::fmt::Display for SkillName {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

/// Issue severity for auditing.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum AuditSeverity {
    Info,
    Warning,
    Error,
    Critical,
}

impl std::fmt::Display for AuditSeverity {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Info => write!(f, "INFO"),
            Self::Warning => write!(f, "WARNING"),
            Self::Error => write!(f, "ERROR"),
            Self::Critical => write!(f, "CRITICAL"),
        }
    }
}

/// A single audit finding.
#[derive(Debug, Clone)]
pub struct AuditIssue {
    pub severity: AuditSeverity,
    pub message: String,
    pub file: Option<String>,
    pub line: Option<usize>,
    pub fix_suggestion: Option<String>,
}

/// Audit a manifest for security issues.
pub fn audit_manifest(manifest: &SkillManifest) -> Vec<AuditIssue> {
    let mut issues = Vec::new();

    // Check for wildcard network domains
    for net in &manifest.permissions.network {
        if net.domain == "*" {
            issues.push(AuditIssue {
                severity: AuditSeverity::Warning,
                message: "Wildcard network domain '*' allows access to any host".into(),
                file: None,
                line: None,
                fix_suggestion: Some(
                    "Restrict to specific domains (e.g., 'api.example.com')".into(),
                ),
            });
        }
        if net.domain.starts_with("*.") {
            issues.push(AuditIssue {
                severity: AuditSeverity::Info,
                message: format!(
                    "Wildcard subdomain '{}' - consider restricting further",
                    net.domain
                ),
                file: None,
                line: None,
                fix_suggestion: None,
            });
        }
    }

    // Check for unrestricted subprocess
    if manifest.permissions.subprocess && manifest.permissions.subprocess_allowlist.is_empty() {
        issues.push(AuditIssue {
            severity: AuditSeverity::Critical,
            message: "Subprocess enabled without allowlist — can execute arbitrary commands".into(),
            file: None,
            line: None,
            fix_suggestion: Some("Add subprocess_allowlist with specific allowed commands".into()),
        });
    }

    // Check for write access to sensitive paths
    for fs in &manifest.permissions.filesystem {
        let is_sensitive = fs.path == "/"
            || fs.path == "/**"
            || fs.path == "${HOME}/**"
            || fs.path.starts_with("/etc");
        let has_write = fs
            .access
            .iter()
            .any(|a| matches!(a, crate::permission::FilesystemAccess::Write));
        if is_sensitive && has_write {
            issues.push(AuditIssue {
                severity: AuditSeverity::Critical,
                message: format!("Write access to sensitive path: {}", fs.path),
                file: None,
                line: None,
                fix_suggestion: Some("Restrict to ${WORKSPACE} or ${TEMP} directories".into()),
            });
        }
    }

    // Check SLSA level
    if manifest.security.slsa_level == 0 {
        issues.push(AuditIssue {
            severity: AuditSeverity::Info,
            message: "SLSA level is 0 (no supply-chain security guarantees)".into(),
            file: None,
            line: None,
            fix_suggestion: Some("Build with --sign to achieve SLSA level 1+".into()),
        });
    }

    // Check for missing description on actions
    for action in &manifest.actions {
        if action.description.is_empty() {
            issues.push(AuditIssue {
                severity: AuditSeverity::Warning,
                message: format!("Action '{}' has no description", action.name),
                file: None,
                line: None,
                fix_suggestion: None,
            });
        }
    }

    issues
}

/// Scan source code for dangerous patterns.
pub fn scan_source_code(content: &str, filename: &str) -> Vec<AuditIssue> {
    let mut issues = Vec::new();

    let dangerous_patterns = [
        ("import os", "Direct os module import — may bypass sandbox"),
        (
            "import subprocess",
            "Direct subprocess import — may bypass sandbox",
        ),
        ("os.system(", "Shell command execution via os.system"),
        ("eval(", "Dynamic code execution via eval()"),
        ("exec(", "Dynamic code execution via exec()"),
        ("__import__(", "Dynamic import — potential sandbox escape"),
        ("ctypes", "C FFI access — potential sandbox escape"),
        (
            "open('/etc/",
            "Direct access to /etc — potential information disclosure",
        ),
        (
            "open(\"/etc/",
            "Direct access to /etc — potential information disclosure",
        ),
    ];

    for (i, line) in content.lines().enumerate() {
        let trimmed = line.trim();
        if trimmed.starts_with('#') {
            continue;
        }
        for (pattern, message) in &dangerous_patterns {
            if trimmed.contains(pattern) {
                issues.push(AuditIssue {
                    severity: AuditSeverity::Warning,
                    message: message.to_string(),
                    file: Some(filename.to_string()),
                    line: Some(i + 1),
                    fix_suggestion: None,
                });
            }
        }
    }

    issues
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_valid_skill_names() {
        assert!(SkillName::new("file-ops").is_ok());
        assert!(SkillName::new("web-fetch").is_ok());
        assert!(SkillName::new("my-skill-v2").is_ok());
        assert!(SkillName::new("ab").is_ok());
    }

    #[test]
    fn test_invalid_skill_names() {
        assert!(SkillName::new("").is_err());
        assert!(SkillName::new("a").is_err());
        assert!(SkillName::new("Invalid").is_err());
        assert!(SkillName::new("has_underscore").is_err());
        assert!(SkillName::new("-starts-dash").is_err());
        assert!(SkillName::new("ends-dash-").is_err());
    }

    #[test]
    fn test_scan_dangerous_code() {
        let code = r#"
import os
import subprocess
result = eval(user_input)
"#;
        let issues = scan_source_code(code, "test.py");
        assert!(issues.len() >= 3);
    }

    #[test]
    fn test_scan_skips_comments() {
        let code = "# import os\nprint('hello')";
        let issues = scan_source_code(code, "test.py");
        assert!(issues.is_empty());
    }
}
