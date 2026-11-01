# Library Research Registry

Records every web library, UI component set, icon set, font, image source, animation
library, or template considered for use. Populated by the researcher agent after web
research; approved items are recorded in `.ufme/DECISIONS.md` before installation.

| Name | Category | Official repo / site | License | Commercial use | Install method | Reason for selection | Status |
|------|----------|---------------------|---------|----------------|----------------|----------------------|--------|

## Research approach (researcher agent)

1. Search the web for candidate libraries matching the project's stack and design goals.
2. For each candidate, verify: official repository, license, commercial-use status, install
   method (npm/CDN), and maintenance activity.
3. Record candidates here with Status = `candidate`.
4. The orchestrator approves/rejects; approved items move to `.ufme/DECISIONS.md` with
   Status = `approved` and are installed project-local only.
5. Rejected items (paid, premium, unverified, non-OSI) are marked `rejected` with reason.

## Example candidates (free & open-source, for reference)

| Name | Category | Official repo / site | License | Commercial use | Install method | Reason for selection | Status |
|------|----------|---------------------|---------|----------------|----------------|----------------------|--------|
| shadcn/ui | UI components | github.com/shadcn/ui | MIT | Yes | npx shadcn-ui add | Accessible, copy-paste, Tailwind + Radix, owned code | candidate |
| Headless UI | Headless components | github.com/tailwindlabs/headlessui | MIT | Yes | npm @headlessui/react | Unstyled, accessible, Tailwind-native | candidate |
| Radix UI | Headless primitives | github.com/radix-ui/primitives | MIT | Yes | npm @radix-ui/react-* | Comprehensive accessible primitives | candidate |
| Mantine | UI components | github.com/mantinedev/mantine | MIT | Yes | npm @mantine/core | 100+ components, hooks, MIT | candidate |
| Lucide | Icons | github.com/lucide-icons/lucide | ISC | Yes | npm lucide-react | Consistent SVG icon set | candidate |
| Phosphor Icons | Icons | github.com/phosphor-icons/react | MIT | Yes | npm @phosphor-icons/react | Flexible weight icons | candidate |
| Inter | Font | github.com/rsms/inter | SIL OFL | Yes | npm @fontsource/inter or CDN | Highly readable UI font | candidate |

Status scale: candidate / approved / rejected
