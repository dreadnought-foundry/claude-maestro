#!/bin/bash
#
# Claude Maestro Installation Script
# Sets up symlinks from ~/.claude to this claude-maestro installation
#
# Usage:
#   ./install.sh              # Install with symlinks (recommended for development)
#   ./install.sh --copy       # Install by copying files (recommended for stability)
#   ./install.sh --uninstall  # Remove installation
#   ./install.sh --status     # Check installation status
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located (claude-maestro root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

# Components to install
COMPONENTS=(
    "agents"
    "commands"
    "scripts"
    "skills"
    "templates"
)

FILES=(
    "sprint-steps.json"
    "WORKFLOW_VERSION"
)

HOOKS=(
    "hooks/pre_tool_use.py"
    "hooks/ralph_loop.py"
    "hooks/session_start.py"
)

print_header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}         ${GREEN}Claude Maestro Installer${NC}                   ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}→${NC} $1"
}

check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check if ~/.claude exists
    if [[ ! -d "$CLAUDE_DIR" ]]; then
        print_warning "~/.claude directory does not exist. Creating it..."
        mkdir -p "$CLAUDE_DIR"
        mkdir -p "$CLAUDE_DIR/hooks"
    fi

    # Check if hooks directory exists
    if [[ ! -d "$CLAUDE_DIR/hooks" ]]; then
        mkdir -p "$CLAUDE_DIR/hooks"
    fi

    print_status "Prerequisites checked"
}

backup_existing() {
    local backup_dir="$CLAUDE_DIR/.backup-maestro-$(date +%Y%m%d-%H%M%S)"
    local needs_backup=false

    # Check if any target exists and is not a symlink to us
    for component in "${COMPONENTS[@]}"; do
        if [[ -e "$CLAUDE_DIR/$component" ]] && [[ ! -L "$CLAUDE_DIR/$component" ]]; then
            needs_backup=true
            break
        fi
    done

    for file in "${FILES[@]}"; do
        if [[ -e "$CLAUDE_DIR/$file" ]] && [[ ! -L "$CLAUDE_DIR/$file" ]]; then
            needs_backup=true
            break
        fi
    done

    if [[ "$needs_backup" == true ]]; then
        print_warning "Backing up existing files to $backup_dir"
        mkdir -p "$backup_dir"

        for component in "${COMPONENTS[@]}"; do
            if [[ -e "$CLAUDE_DIR/$component" ]] && [[ ! -L "$CLAUDE_DIR/$component" ]]; then
                mv "$CLAUDE_DIR/$component" "$backup_dir/"
                print_info "Backed up: $component"
            fi
        done

        for file in "${FILES[@]}"; do
            if [[ -e "$CLAUDE_DIR/$file" ]] && [[ ! -L "$CLAUDE_DIR/$file" ]]; then
                mv "$CLAUDE_DIR/$file" "$backup_dir/"
                print_info "Backed up: $file"
            fi
        done

        print_status "Backup created at: $backup_dir"
    fi
}

remove_existing_links() {
    for component in "${COMPONENTS[@]}"; do
        if [[ -L "$CLAUDE_DIR/$component" ]]; then
            rm "$CLAUDE_DIR/$component"
        fi
    done

    for file in "${FILES[@]}"; do
        if [[ -L "$CLAUDE_DIR/$file" ]]; then
            rm "$CLAUDE_DIR/$file"
        fi
    done
}

save_source_path() {
    # Save the source path so maestro-update can find it later
    echo "$SCRIPT_DIR" > "$CLAUDE_DIR/maestro-source"
    print_status "Saved source path: $SCRIPT_DIR"
}

install_symlinks() {
    print_info "Installing with symlinks..."

    backup_existing
    remove_existing_links
    save_source_path

    # Create symlinks for directories
    for component in "${COMPONENTS[@]}"; do
        if [[ -d "$SCRIPT_DIR/$component" ]]; then
            ln -s "$SCRIPT_DIR/$component" "$CLAUDE_DIR/$component"
            print_status "Linked: $component -> $SCRIPT_DIR/$component"
        else
            print_warning "Skipped: $component (not found in source)"
        fi
    done

    # Create symlinks for files
    for file in "${FILES[@]}"; do
        if [[ -f "$SCRIPT_DIR/$file" ]]; then
            ln -s "$SCRIPT_DIR/$file" "$CLAUDE_DIR/$file"
            print_status "Linked: $file -> $SCRIPT_DIR/$file"
        else
            print_warning "Skipped: $file (not found in source)"
        fi
    done

    # Copy hooks (not symlink - they may need local customization)
    install_hooks
}

install_copy() {
    print_info "Installing by copying files..."

    backup_existing
    remove_existing_links
    save_source_path

    # Copy directories
    for component in "${COMPONENTS[@]}"; do
        if [[ -d "$SCRIPT_DIR/$component" ]]; then
            cp -r "$SCRIPT_DIR/$component" "$CLAUDE_DIR/$component"
            print_status "Copied: $component"
        else
            print_warning "Skipped: $component (not found in source)"
        fi
    done

    # Copy files
    for file in "${FILES[@]}"; do
        if [[ -f "$SCRIPT_DIR/$file" ]]; then
            cp "$SCRIPT_DIR/$file" "$CLAUDE_DIR/$file"
            print_status "Copied: $file"
        else
            print_warning "Skipped: $file (not found in source)"
        fi
    done

    # Copy hooks
    install_hooks
}

install_hooks() {
    print_info "Installing hooks..."

    for hook in "${HOOKS[@]}"; do
        local hook_file=$(basename "$hook")
        if [[ -f "$SCRIPT_DIR/$hook" ]]; then
            # Only copy if target doesn't exist or is different
            if [[ ! -f "$CLAUDE_DIR/hooks/$hook_file" ]] || ! diff -q "$SCRIPT_DIR/$hook" "$CLAUDE_DIR/hooks/$hook_file" > /dev/null 2>&1; then
                cp "$SCRIPT_DIR/$hook" "$CLAUDE_DIR/hooks/$hook_file"
                chmod +x "$CLAUDE_DIR/hooks/$hook_file"
                print_status "Installed hook: $hook_file"
            else
                print_info "Hook unchanged: $hook_file"
            fi
        fi
    done
}

uninstall() {
    print_info "Uninstalling claude-maestro..."

    # Remove symlinks/directories we created
    for component in "${COMPONENTS[@]}"; do
        if [[ -L "$CLAUDE_DIR/$component" ]]; then
            rm "$CLAUDE_DIR/$component"
            print_status "Removed link: $component"
        elif [[ -d "$CLAUDE_DIR/$component" ]]; then
            print_warning "Skipped: $component (not a symlink - may be user data)"
        fi
    done

    for file in "${FILES[@]}"; do
        if [[ -L "$CLAUDE_DIR/$file" ]]; then
            rm "$CLAUDE_DIR/$file"
            print_status "Removed link: $file"
        fi
    done

    # Don't remove hooks - they may have been customized
    print_warning "Hooks were not removed (may be customized). Remove manually if needed:"
    for hook in "${HOOKS[@]}"; do
        local hook_file=$(basename "$hook")
        echo "    rm ~/.claude/hooks/$hook_file"
    done

    print_status "Uninstall complete"
}

show_status() {
    print_info "Installation status:"
    echo ""

    local all_ok=true

    for component in "${COMPONENTS[@]}"; do
        if [[ -L "$CLAUDE_DIR/$component" ]]; then
            local target=$(readlink "$CLAUDE_DIR/$component")
            if [[ "$target" == "$SCRIPT_DIR/$component" ]]; then
                print_status "$component: symlinked (current)"
            else
                print_warning "$component: symlinked to different location: $target"
            fi
        elif [[ -d "$CLAUDE_DIR/$component" ]]; then
            print_info "$component: copied (not symlinked)"
        else
            print_error "$component: not installed"
            all_ok=false
        fi
    done

    for file in "${FILES[@]}"; do
        if [[ -L "$CLAUDE_DIR/$file" ]]; then
            local target=$(readlink "$CLAUDE_DIR/$file")
            if [[ "$target" == "$SCRIPT_DIR/$file" ]]; then
                print_status "$file: symlinked (current)"
            else
                print_warning "$file: symlinked to different location: $target"
            fi
        elif [[ -f "$CLAUDE_DIR/$file" ]]; then
            print_info "$file: copied (not symlinked)"
        else
            print_error "$file: not installed"
            all_ok=false
        fi
    done

    echo ""
    echo "Hooks:"
    for hook in "${HOOKS[@]}"; do
        local hook_file=$(basename "$hook")
        if [[ -f "$CLAUDE_DIR/hooks/$hook_file" ]]; then
            print_status "hooks/$hook_file: installed"
        else
            print_warning "hooks/$hook_file: not installed"
        fi
    done

    echo ""
    if [[ "$all_ok" == true ]]; then
        print_status "Claude Maestro is installed and ready!"
    else
        print_warning "Some components are missing. Run ./install.sh to fix."
    fi
}

show_help() {
    echo "Claude Maestro Installation Script"
    echo ""
    echo "Usage:"
    echo "  ./install.sh              Install with symlinks (recommended for development)"
    echo "  ./install.sh --copy       Install by copying files (recommended for stability)"
    echo "  ./install.sh --uninstall  Remove installation"
    echo "  ./install.sh --status     Check installation status"
    echo "  ./install.sh --help       Show this help"
    echo ""
    echo "Symlink mode (default):"
    echo "  - Changes in claude-maestro immediately reflect in ~/.claude"
    echo "  - Best for developers and maintainers"
    echo "  - Requires claude-maestro to remain at current path"
    echo ""
    echo "Copy mode:"
    echo "  - Files are copied to ~/.claude"
    echo "  - More stable, doesn't depend on source location"
    echo "  - Run ./install.sh --copy again to update"
    echo ""
    echo "After installation, use these commands in any project:"
    echo "  /project-create    Initialize a project with sprint workflow"
    echo "  /project-update    Sync latest workflow updates to project"
    echo ""
}

print_post_install() {
    echo ""
    echo -e "${GREEN}Installation complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Open a new terminal or restart Claude Code"
    echo "  2. Navigate to your project directory"
    echo "  3. Run: /project-create"
    echo ""
    echo "Available commands after installation:"
    echo "  /project-create     Initialize project with sprint workflow"
    echo "  /project-update     Sync latest workflow to project"
    echo "  /sprint-new         Create a new sprint"
    echo "  /sprint-start N     Start working on sprint N"
    echo "  /sprint-status      Check sprint progress"
    echo ""
    echo "Source: $SCRIPT_DIR"
    echo "Target: $CLAUDE_DIR"
    echo ""
}

# Main
print_header

case "${1:-}" in
    --help|-h)
        show_help
        ;;
    --uninstall)
        check_prerequisites
        uninstall
        ;;
    --status)
        show_status
        ;;
    --copy)
        check_prerequisites
        install_copy
        print_post_install
        ;;
    ""|--symlink)
        check_prerequisites
        install_symlinks
        print_post_install
        ;;
    *)
        print_error "Unknown option: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
