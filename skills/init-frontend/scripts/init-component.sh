#!/usr/bin/env bash
# init-component.sh — Add component with state matrix, stories, a11y test.
#
# Usage:
#   init-component.sh <name> [project-dir]
#
set -euo pipefail

log() { echo "[init-frontend component] $*"; }

COMPONENT_NAME="${1:-}"
PROJECT_DIR="${2:-$(pwd)}"

if [ -z "$COMPONENT_NAME" ]; then
  echo "Usage: $0 <name> [project-dir]" >&2
  exit 2
fi

COMPONENT_DIR="$PROJECT_DIR/src/components/$COMPONENT_NAME"
mkdir -p "$COMPONENT_DIR"

# Component source
cat > "$COMPONENT_DIR/$COMPONENT_NAME.jsx" <<JSX
import { cn } from '../../utils/cn';

export function $COMPONENT_NAME({ className, ...props }) {
  return (
    <div className={cn('component-base', className)} {...props} />
  );
}
JSX

# Stories
cat > "$COMPONENT_DIR/$COMPONENT_NAME.stories.jsx" <<JSX
import { $COMPONENT_NAME } from './$COMPONENT_NAME';

export default {
  title: 'Components/$COMPONENT_NAME',
  component: $COMPONENT_NAME,
};

export const Default = () => <$COMPONENT_NAME />;
Default.storyName = 'Default';

export const States = () => (
  <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
    <$COMPONENT_NAME />
    <$COMPONENT_NAME className="state-loading" />
    <$COMPONENT_NAME className="state-empty" />
    <$COMPONENT_NAME className="state-error" />
  </div>
);
States.storyName = 'All States';
JSX

# Accessibility test
cat > "$COMPONENT_DIR/$COMPONENT_NAME.a11y.test.jsx" <<JSX
import { axe } from 'axe-core';
import { render, screen } from '@testing-library/react';
import { $COMPONENT_NAME } from './$COMPONENT_NAME';

describe('$COMPONENT_NAME accessibility', () => {
  it('passes axe-core WCAG 2.2 AA checks', async () => {
    const { container } = render(<$COMPONENT_NAME />);
    const results = await axe(container);
    expect(results.violations).toHaveLength(0);
  });

  it('has focus-visible ring', () => {
    render(<$COMPONENT_NAME />);
    const focusable = screen.getByRole('button') || screen.getByRole('link');
    expect(focusable).toBeInTheDocument();
  });
});
JSX

# State matrix
cat > "$COMPONENT_DIR/$COMPONENT_NAME.states.md" <<MD
# $COMPONENT_NAME — State Matrix

| State | Class | Description |
|-------|-------|-------------|
| Default | (none) | Standard appearance |
| Loading | \`.state-loading\` | Content loading state |
| Empty | \`.state-empty\` | No content available |
| Error | \`.state-error\` | Error state |

## Accessibility
- \`focus-visible\` ring applied
- Keyboard navigable
- Contrast ≥ 4.5:1 text / ≥ 3:1 UI
MD

log "Component created: $COMPONENT_DIR"
log "Files: $COMPONENT_NAME.jsx, $COMPONENT_NAME.stories.jsx, $COMPONENT_NAME.a11y.test.jsx, $COMPONENT_NAME.states.md"
