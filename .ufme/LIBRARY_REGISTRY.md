# Library Research Registry

Registry of frontend libraries, UI component systems, icons, fonts, image sources,
animation tools, charts, and templates considered by UFME. Entries are research candidates,
not automatic install approvals. The researcher agent should verify the exact version,
framework compatibility, package provenance, license text, maintenance status, and project fit
before recommending installation. Approved decisions belong in `.ufme/DECISIONS.md`.

**Status meanings:** `candidate` = potential option; `researched` = official documentation/source checked;
`approved` = explicitly selected for a project; `rejected` = not suitable for the stated context.
A registry entry does not mean the dependency is installed or tested.

## Registry

| Name | Category | Official repo / site | License / terms | Commercial use | Install / use | Reason for selection | Status |
|------|----------|---------------------|-----------------|----------------|---------------|---------------------|--------|
| tailwindcss | CSS framework | https://tailwindcss.com | MIT (verify package license) | Generally yes under MIT | `npm install -D tailwindcss` | Utility-first styling; responsive design tokens and rapid iteration | researched |
| @mantine/core | Styled React components | https://mantine.dev/ | MIT | Generally yes under MIT | `npm install @mantine/core` | Broad component set and hooks for React applications | candidate |
| motion | Animation | https://motion.dev/ | MIT (verify current package) | Generally yes under MIT | `npm install motion` | Declarative React animations and gestures | candidate |
| gsap | Animation | https://gsap.com | GSAP Standard License; not simply MIT | Verify current license and product-specific terms | `npm install gsap` | Timeline, scroll-triggered and complex motion; licensing requires explicit review | researched |
| lucide-react | Icons | https://lucide.dev | ISC | Generally yes under ISC | `npm install lucide-react` | Consistent outline icons with React components | candidate |
| @phosphor-icons/react | Icons | https://phosphoricons.com | MIT | Generally yes under MIT | `npm install @phosphor-icons/react` | Multiple weights/styles for visual hierarchy | candidate |
| recharts | Charts | https://github.com/recharts/recharts | MIT | Generally yes under MIT | `npm install recharts` | Composable React charts; SVG-based | researched |
| @radix-ui/react-dialog | Headless primitive | https://www.radix-ui.com/primitives | MIT | Generally yes under MIT | `npm install @radix-ui/react-dialog` | Accessible dialog behavior without imposing styling | candidate |
| shadcn/ui | Copy-in component system | https://ui.shadcn.com/ | MIT for upstream project; audit each registry component/dependency | Generally yes; check included assets/dependencies | `npx shadcn@latest init` then add selected components | Editable source, composable components, strong AI-agent inspectability | researched |
| Base UI | Headless React primitives | https://base-ui.com/ | MIT (verify package) | Generally yes under MIT | `npm install @base-ui/react` | Accessible unstyled primitives; suitable when design system owns styling | researched |
| Ark UI | Headless multi-framework components | https://ark-ui.com/ | MIT (verify package) | Generally yes under MIT | Install framework-specific package per docs | React, Vue, Solid and Svelte support; state-machine-backed behavior | candidate |
| React Aria Components | Accessible components | https://react-spectrum.adobe.com/react-aria/ | Apache-2.0 (verify package) | Generally yes under Apache-2.0 | `npm install react-aria-components` | Accessibility and internationalization-oriented primitives | candidate |
| Headless UI | Headless components | https://headlessui.com/ | MIT | Generally yes under MIT | `npm install @headlessui/react` or Vue package | Tailwind-friendly accessible interaction primitives | candidate |
| @mui/material | Styled React components | https://mui.com/material-ui/ | MIT | Generally yes under MIT | `npm install @mui/material @emotion/react @emotion/styled` | Mature, broad component suite; Material Design visual language | candidate |
| @chakra-ui/react | Styled React components | https://chakra-ui.com/ | MIT (verify current release) | Generally yes under MIT | Follow current installation docs | Theme tokens, recipes and accessible component system | candidate |
| daisyui | Tailwind component plugin | https://daisyui.com/ | MIT | Generally yes under MIT | `npm install -D daisyui` | Fast semantic component classes and themes; evaluate visual distinctiveness | candidate |
| @tabler/icons-react | Icons | https://github.com/tabler/tabler-icons | MIT | Generally yes under MIT | `npm install @tabler/icons-react` | Large outline/filled icon set and React package | researched |
| @heroicons/react | Icons | https://github.com/tailwindlabs/heroicons | MIT | Generally yes under MIT | `npm install @heroicons/react` | Compact icon family aligned with Tailwind ecosystem | candidate |
| @nivo/* | Charts | https://nivo.rocks/ | MIT (verify selected package) | Generally yes under MIT | Install only needed Nivo packages | Rich React data visualizations and responsive charts | candidate |
| echarts | Charts | https://echarts.apache.org/ | Apache-2.0 (verify package) | Generally yes under Apache-2.0 | `npm install echarts` | Broad chart types and high-volume visualization options | candidate |
| @google/fonts (Google Fonts) | Fonts | https://fonts.google.com/ | Font-specific licenses; commonly OFL, verify each family | Usually permitted under the specific font license | Self-host or use official CSS/API | Broad typography selection; record exact family and license | researched |
| Unsplash | Image source/API | https://unsplash.com/ | Unsplash License for images; API terms add requirements | Generally allowed under image license, subject to restrictions | API requires developer registration; use API docs | Photography source; API attribution/hotlinking and usage constraints must be honored | researched |
| Pexels | Image/video source | https://www.pexels.com/ | Pexels License and Terms; content-specific restrictions | Generally allowed subject to terms | API requires key; follow official API docs | Photo/video assets; track attribution, model/property and standalone-use restrictions | candidate |
| dotLottie Web | Animation player | https://github.com/LottieFiles/dotlottie-web | Verify repository/package license and each animation asset license separately | Verify asset license | Install package per official docs | Efficient vector animation player; use only licensed animation files | candidate |
| React Email | Email templates | https://react.email/ | Verify project and each template's license | Verify template/dependency license | Follow official docs | Reusable email layout templates and React-based authoring | researched |
| shadcn registry ecosystem | Component/template registry | https://ui.shadcn.com/docs/registry | Registry/component-specific; do not assume every third-party item is MIT | Verify each item | Use official CLI only after inspecting registry metadata/source | Discover reusable blocks and components; provenance and dependency review required | researched |

## Research findings and selection guidance

### Component systems
- **Default discovery path:** inspect shadcn/ui and its official registry directory for editable, project-local components. It is a code-distribution approach rather than a conventional runtime component package; review generated source and dependencies before accepting.
- **Primitive-first alternatives:** Base UI, Radix, React Aria, Headless UI, and Ark UI. Choose based on framework support, accessibility needs, API stability, and the existing project's design system.
- **Styled-system alternatives:** Mantine, MUI, Chakra, and daisyUI. Prefer one primary styled system per project; mixing systems can create inconsistent tokens, CSS and interaction patterns.
- **Important current ecosystem note:** shadcn/ui documents Base UI as a default option for new projects while continuing to support Radix. Do not migrate an existing project solely because the default changed; evaluate the current project's installed primitive layer first.

### Assets and licensing
- Record the exact package/version or asset URL, source author, license identifier, license URL, attribution requirement, retrieval date, and any model/property/trademark restrictions.
- **Fonts:** license is family-specific; do not label all Google Fonts as one license. Preserve the font's license file when self-hosting.
- **Stock images/video:** distinguish a site's general content license from its API terms. Unsplash API integrations require hotlinked API image URLs and photographer/Unsplash attribution; API credentials must remain server-side when necessary. Pexels content is subject to its license and terms, including restrictions on standalone redistribution.
- **Animation:** the player library's license does not license the animation JSON/Lottie asset. Track both separately.
- **GSAP:** do not mark commercial use as a blanket “yes.” Its Standard License is not an MIT license; verify the use case and current license terms.

### Automated researcher acceptance checklist
Before adding or recommending an entry, the researcher should:
1. Prefer official project documentation, repository, package metadata and license files over third-party roundups.
2. Confirm framework/version compatibility, package name, install command, maintenance/release activity and known security advisories.
3. Read the exact license and any separate asset/API terms; use `Verify` where scope is uncertain.
4. Explain the specific use case and alternatives; avoid recommending multiple overlapping component systems without a reason.
5. Record evidence URLs and the date checked. Mark claims as documented, prototype-tested, or production-verified—never imply a test was run if it was not.
6. Avoid adding dependencies automatically. Present a shortlist and obtain project approval before installation or code generation from third-party registries.
7. For generated/copied code, preserve required notices and review transitive dependencies, scripts, remote assets and security implications.

## Official research sources

- shadcn/ui overview and open-code model: https://ui.shadcn.com/docs
- shadcn/ui official site/source verification: https://ui.shadcn.com/docs/official
- shadcn/ui registry directory: https://ui.shadcn.com/docs/registry
- shadcn/ui Base UI/Radix changelog: https://ui.shadcn.com/docs/changelog/2026-07-base-ui-default
- Base UI overview: https://base-ui.com/react/overview/about
- Ark UI overview: https://ark-ui.com/docs/overview/about
- Tailwind CSS repository/license: https://github.com/tailwindlabs/tailwindcss
- GSAP repository and standard license: https://github.com/greensock/GSAP ; https://gsap.com/standard-license
- Recharts repository/docs: https://github.com/recharts/recharts ; https://recharts.github.io/
- Tabler Icons repository/license: https://github.com/tabler/tabler-icons
- MUI repository/license: https://github.com/mui/material-ui
- Unsplash license/API terms/docs/guidelines: https://unsplash.com/license ; https://unsplash.com/api-terms ; https://unsplash.com/documentation ; https://help.unsplash.com/en/articles/2511245-unsplash-api-guidelines
- Pexels terms/license: https://www.pexels.com/license ; https://www.pexels.com/terms-of-service
- Google Fonts: https://fonts.google.com/
- React Email templates: https://react.email/templates
- LottieFiles web player: https://github.com/LottieFiles/dotlottie-web

## Governance
This registry is a research index, not a dependency lockfile or blanket legal opinion. Project decisions must cite the specific entry and context in `.ufme/DECISIONS.md`. Re-check licenses, package names, versions, APIs, and terms at implementation time because they can change. Use the narrowest dependency set that meets the design and functional requirements.
