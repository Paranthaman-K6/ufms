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

| react-hook-form | React form state | https://react-hook-form.com/ | MIT | Generally yes under MIT | `npm install react-hook-form` | Performant, uncontrolled-first form state; supports schema resolvers | researched |
| @tanstack/react-form | Multi-framework form state | https://tanstack.com/form/latest | MIT | Generally yes under MIT | `npm install @tanstack/react-form` | Type-safe, composable forms; React/Vue/Solid/Angular adapters | researched |
| formik | React form state | https://formik.org/ | MIT | Generally yes under MIT | `npm install formik` | Established form state, validation and submission abstraction; useful in existing Formik projects | candidate |
| final-form | Framework-agnostic form state | https://final-form.org/ | MIT | Generally yes under MIT | `npm install final-form` | Subscription-based form state core | candidate |
| react-final-form | React adapter | https://final-form.org/react | MIT | Generally yes under MIT | `npm install react-final-form final-form` | React bindings for Final Form; field-level subscriptions | candidate |
| @ngx-formly/core | Angular schema-driven forms | https://formly.dev/ | MIT (verify selected packages) | Generally yes under MIT | `npm install @ngx-formly/core` plus framework adapter | JSON/schema-driven dynamic Angular forms and custom field types | researched |
| survey-core / survey-react-ui | Cross-framework dynamic forms/surveys | https://surveyjs.io/form-library/documentation/overview | MIT for Form Library | Generally yes under MIT | `npm install survey-react-ui` (or Angular/Vue/vanilla package) | JSON-driven multi-page forms, conditional logic, surveys and quizzes | researched |
| vee-validate | Vue form state/validation | https://vee-validate.logaretm.com/ | MIT | Generally yes under MIT | `npm install vee-validate` | Vue-native form validation and schema integrations | candidate |
| @vuelidate/core | Vue validation | https://vuelidate-next.netlify.app/ | MIT | Generally yes under MIT | `npm install @vuelidate/core` | Lightweight model-based validation for Vue | candidate |
| Felte | Svelte form state | https://felte.dev/ | MIT (verify current package) | Generally yes under MIT | Follow official Svelte installation docs | Svelte-oriented form handling with validator adapters | candidate |
| sveltekit-superforms | SvelteKit form handling | https://superforms.rocks/ | MIT (verify package) | Generally yes under MIT | Follow official SvelteKit docs | Server/client validation, progressive enhancement and form actions | candidate |
| Angular Reactive Forms | Angular built-in forms API | https://angular.dev/guide/forms/reactive-forms | Angular framework license (MIT) | Generally yes under MIT | Built into Angular | Model-driven forms, validation and dynamic controls without third-party dependency | researched |
| Zod | Schema validation | https://zod.dev/ | MIT | Generally yes under MIT | `npm install zod` | Type inference and runtime validation; integrates with form libraries | researched |
| Valibot | Schema validation | https://valibot.dev/ | MIT | Generally yes under MIT | `npm install valibot` | Modular/tree-shakeable validation schemas | researched |
| Yup | Schema validation | https://github.com/jquense/yup | MIT | Generally yes under MIT | `npm install yup` | Mature schema validation, widely used with Formik and resolvers | candidate |
| Ajv | JSON Schema validation | https://ajv.js.org/ | MIT | Generally yes under MIT | `npm install ajv` | Fast JSON Schema validation for API contracts and generated forms | researched |
| @rjsf/core | JSON Schema forms (React) | https://github.com/rjsf-team/react-jsonschema-form | Apache-2.0 (verify packages) | Generally yes under Apache-2.0 | `npm install @rjsf/core` plus theme package | Render React forms from JSON Schema with extensible widgets | researched |
| FormKit | Vue form system | https://formkit.com/ | MIT for core (verify add-ons) | Generally yes under MIT for core | `npm install @formkit/vue` | Vue form inputs, validation and schema-based form generation | candidate |

## External discovery directories

These directories are **discovery inputs**, not authority for package quality, licensing, or security. The researcher must follow each candidate to its official repository/docs and verify it independently before adding a library row or recommending use.

| Directory | Scope observed | How UFME should use it | Important limitation | Status |
|-----------|---------------|------------------------|----------------------|--------|
| DevTools.tools | Browser-based developer utilities; categories include design, visual, security, network/API, generators, data processing and AI utilities | Discover workflow helpers for color/contrast checks, schema generation, API/network debugging, image/visual utilities and prompt/context preparation; record useful tool URLs in project research notes | Primarily an online utility directory, not a catalog of installable open-source frontend packages. Verify privacy claims and whether processing is local before pasting project/customer data | researched |
| free-for.dev | Free-tier SaaS/PaaS/IaaS and developer services; categories include testing/QA, API tools, design tools, fonts, forms/surveys, hosting, storage/media, analytics, security and AI | Discover hosted services for prototyping, preview deployments, form endpoints, API mocking/testing, visual QA, assets and monitoring when a project has a zero-cost constraint | A free tier is **not** the same as open source, self-hostable, unlimited, or production-suitable. Record plan limits, commercial restrictions, data handling, vendor lock-in and current terms | researched |
| free-for.dev source repository | Community-maintained service list: https://github.com/ripienaar/free-for-dev | Prefer repository entries/PR history as a traceable source when investigating listed services; then verify the provider's own pricing, docs, terms and privacy policy | Repository is a curated directory, not a warranty or license approval for listed vendors | researched |

### Research workflow for directory-sourced candidates
1. Use the directory to discover a candidate and its category; do not copy claims as verified facts.
2. Follow through to the official provider/repository, package registry, license, pricing/free-tier page, docs and security advisories.
3. Classify the candidate as one of: open-source library, open-source self-hosted tool, hosted free-tier service, browser utility, template/asset source, or paid/commercial product.
4. For hosted services, record the current free allowance and limits (quotas, retention, inactivity/sleep, build minutes, bandwidth, seats, commercial-use scope, and required payment method) with a checked date.
5. For browser utilities, assess whether input is processed locally or uploaded; do not send secrets, private source, customer data, credentials, or production payloads.
6. Only convert a directory-sourced candidate into a library row after checking package identity, framework compatibility, maintenance, license and install instructions.

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


### Form libraries: selection notes
- **React default shortlist:** React Hook Form for a conventional React form workflow; TanStack Form for strongly typed, composable forms and cross-framework reuse; Formik mainly for established projects already using it.
- **Dynamic/schema-driven forms:** SurveyJS Form Library for complex surveys and conditional multi-step flows; RJSF when JSON Schema is the source of truth and React is the renderer; Angular Formly for Angular schema-driven forms.
- **Framework-native options:** Angular Reactive Forms, vee-validate/Vuelidate for Vue, and Felte/SvelteKit Superforms for Svelte. Prefer framework-native integrations over wrapping a React library into another framework.
- **Validation is a separate decision:** Zod, Valibot, Yup and Ajv are validators, not complete form-state libraries. Pick one schema system where possible and check whether the chosen form library supports it directly or through a resolver/Standard Schema adapter.
- **Open-source scope:** SurveyJS Form Library is MIT, but Survey Creator/other products may have separate licensing. For all monorepos, verify the license of the exact package and optional commercial add-ons.
- **Avoid duplication:** do not add multiple form-state libraries to one project without a migration or clear feature boundary. Avoid combining schema validators unnecessarily.

### Official form-library sources
- React Hook Form docs and repository/license: https://react-hook-form.com/ ; https://github.com/react-hook-form/react-hook-form
- TanStack Form docs and repository: https://tanstack.com/form/latest/docs/framework/react/quick-start ; https://github.com/TanStack/form
- Formik docs: https://formik.org/docs/overview
- Final Form: https://final-form.org/ ; React Final Form: https://final-form.org/react
- SurveyJS Form Library docs/license: https://surveyjs.io/form-library/documentation/overview ; https://github.com/surveyjs/survey-library
- Angular Reactive Forms: https://angular.dev/guide/forms/reactive-forms
- Angular Formly: https://formly.dev/ ; https://github.com/ngx-formly/ngx-formly
- vee-validate: https://vee-validate.logaretm.com/ ; Vuelidate: https://vuelidate-next.netlify.app/
- Felte: https://felte.dev/ ; SvelteKit Superforms: https://superforms.rocks/
- React JSON Schema Form: https://github.com/rjsf-team/react-jsonschema-form
- FormKit: https://formkit.com/ ; https://github.com/formkit/formkit
- Zod: https://zod.dev/ ; Valibot: https://valibot.dev/ ; Yup: https://github.com/jquense/yup ; Ajv: https://ajv.js.org/

## Governance
This registry is a research index, not a dependency lockfile or blanket legal opinion. Project decisions must cite the specific entry and context in `.ufme/DECISIONS.md`. Re-check licenses, package names, versions, APIs, and terms at implementation time because they can change. Use the narrowest dependency set that meets the design and functional requirements.
