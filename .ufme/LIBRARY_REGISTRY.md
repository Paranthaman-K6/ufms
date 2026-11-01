# Library Research Registry

Registry of frontend libraries, UI component systems, icons, fonts, image sources,
animation tools, charts, templates, hosted developer services, and browser utilities considered by UFME. Entries are research candidates,
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

## Form libraries and validation

These are software dependencies or framework APIs that can be installed or integrated into a project.

| Name | Category | Official repo / site | License / terms | Install / use | Reason for selection | Status |
|------|----------|----------------------|-----------------|---------------|---------------------|--------|
| react-hook-form | React form state | https://react-hook-form.com/ | MIT | `npm install react-hook-form` | Performant, uncontrolled-first form state; supports schema resolvers | researched |
| @tanstack/react-form | Multi-framework form state | https://tanstack.com/form/latest | MIT | `npm install @tanstack/react-form` | Type-safe, composable forms with framework adapters | researched |
| formik | React form state | https://formik.org/ | MIT | `npm install formik` | Established form state, validation and submission abstraction; useful in existing Formik projects | candidate |
| final-form | Framework-agnostic form state | https://final-form.org/ | MIT | `npm install final-form` | Subscription-based form state core | candidate |
| react-final-form | React adapter | https://final-form.org/react | MIT | `npm install react-final-form final-form` | React bindings for Final Form; field-level subscriptions | candidate |
| @ngx-formly/core | Angular schema-driven forms | https://formly.dev/ | MIT (verify selected packages) | Install core plus Angular adapter per docs | JSON/schema-driven dynamic Angular forms and custom field types | researched |
| survey-core / survey-react-ui | Cross-framework dynamic forms/surveys | https://surveyjs.io/form-library/documentation/overview | MIT for Form Library; other products may differ | Install framework-specific package per docs | JSON-driven multi-page forms, conditional logic, surveys and quizzes | researched |
| vee-validate | Vue form state/validation | https://vee-validate.logaretm.com/ | MIT | `npm install vee-validate` | Vue-native form validation and schema integrations | candidate |
| @vuelidate/core | Vue validation | https://vuelidate-next.netlify.app/ | MIT | `npm install @vuelidate/core` | Lightweight model-based validation for Vue | candidate |
| Felte | Svelte form state | https://felte.dev/ | MIT (verify current package) | Follow official Svelte installation docs | Svelte-oriented form handling with validator adapters | candidate |
| sveltekit-superforms | SvelteKit form handling | https://superforms.rocks/ | MIT (verify package) | Follow official SvelteKit docs | Server/client validation, progressive enhancement and form actions | candidate |
| Angular Reactive Forms | Angular built-in forms API | https://angular.dev/guide/forms/reactive-forms | Angular framework license (MIT) | Built into Angular | Model-driven forms, validation and dynamic controls without third-party dependency | researched |
| Zod | Schema validation | https://zod.dev/ | MIT | `npm install zod` | Type inference and runtime validation; integrates with form libraries | researched |
| Valibot | Schema validation | https://valibot.dev/ | MIT | `npm install valibot` | Modular/tree-shakeable validation schemas | researched |
| Yup | Schema validation | https://github.com/jquense/yup | MIT | `npm install yup` | Mature schema validation, widely used with Formik and resolvers | candidate |
| Ajv | JSON Schema validation | https://ajv.js.org/ | MIT | `npm install ajv` | Fast JSON Schema validation for API contracts and generated forms | researched |
| @rjsf/core | JSON Schema forms (React) | https://github.com/rjsf-team/react-jsonschema-form | Apache-2.0 (verify selected packages) | `npm install @rjsf/core` plus a theme package | Render React forms from JSON Schema with extensible widgets | researched |
| FormKit | Vue form system | https://formkit.com/ | MIT for core; verify add-ons | `npm install @formkit/vue` | Vue form inputs, validation and schema-based form generation | candidate |


## Actual provider websites and developer tools

The following entries link to actual product, documentation, pricing, or project sites—not back to discovery directories. Each item is classified as a library, open-source tool, hosted service, or browser utility. A hosted free tier does not make a product open source.

### Browser utilities, design, and asset creation

| Name | Category | Actual site | Open-source / plan status | UFME use and cautions |
|------|----------|-------------|---------------------------|-----------------------|
| WebAIM Contrast Checker | Color contrast | https://webaim.org/resources/contrastchecker/ | Free browser utility | Check text and component color pairs; it does not scan an entire application |
| WAVE | Accessibility evaluation | https://wave.webaim.org/ | Free browser checker and browser extensions; subscription/API options | Use on public pages; use the extension for authenticated/local pages. Automated output still requires human accessibility review |
| Haikei | SVG/background generator | https://haikei.app/ | Free web tool; verify current export/usage terms | Generate wave, blob, grid, gradient and other vector assets; inspect output and asset terms |
| Squoosh | Image compression | https://squoosh.app/ | Open-source project; Apache-2.0 repository | Compress and compare images locally in the browser; project documentation says images are not uploaded |
| Excalidraw | Diagramming / whiteboard | https://excalidraw.com/ | Open-source application; verify repository license before embedding/reusing code | Create user flows, system diagrams, wireframes and architecture sketches |
| Figma | UI design / prototyping | https://www.figma.com/ | Proprietary; Starter plan has limited free access | Design systems, wireframes, prototypes and design handoff; plan limits apply |
| Boxy SVG | SVG editor | https://boxy-svg.com/ | Proprietary application; review its current pricing and terms | Edit SVG icons and illustrations; do not assume all features or exports are free |
| Bunny Fonts | Privacy-oriented font delivery | https://fonts.bunny.net/ | Font collection is open source; each family has its own license | Privacy-oriented alternative for delivering web fonts; vendor states requests are not logged, but check each family license |
| Fontshare | Font library | https://www.fontshare.com/ | Free service; font-specific license terms apply | Discover type families; keep each family’s license and attribution terms with the project |
| Font Squirrel | Font library | https://www.fontsquirrel.com/ | Font-specific licenses; verify each font's web-embedding rights | Discover fonts with commercial-use indications; the provider itself advises reading each font license |
| Google Fonts | Font library | https://fonts.google.com/ | Family-specific open licenses, commonly OFL; verify each family | Discover, self-host or load web fonts; retain license notices and avoid assuming one license covers every family |

### API, data, and debugging utilities

| Name | Category | Actual site / docs | Open-source / plan status | UFME use and cautions |
|------|----------|--------------------|---------------------------|-----------------------|
| Hoppscotch | API client and mocking | https://hoppscotch.com/ | Open-source project with hosted and self-hosted options; verify edition and package licenses | Test REST, GraphQL and other API workflows; do not commit real API secrets in shared collections |
| Swagger Editor | OpenAPI editor | https://editor.swagger.io/ | Open-source editor project; verify repository license and version | Draft, validate and preview OpenAPI documents before generating frontend API clients |
| JSON Crack | JSON visualization | https://jsoncrack.com/ | Hosted browser tool; verify current privacy and source/license terms | Visualize nested JSON/API responses; do not upload credentials or private production payloads |
| JSON Editor Online | JSON editor / validator | https://jsoneditoronline.org/ | Hosted tool; verify data-processing/privacy terms | Inspect, format and compare JSON fixtures and API payloads |
| CyberChef | Encoding / data transformation | https://gchq.github.io/CyberChef/ | Open-source; Apache-2.0 | Encode, decode, hash, parse and transform sample data; do not treat it as a substitute for secure application code |
| Regex101 | Regular-expression debugger | https://regex101.com/ | Hosted browser utility | Test regex patterns, explain matches and check language-specific regex flavors; avoid pasting private data |
| JWT.io Debugger | JWT inspection | https://jwt.io/ | Hosted browser utility | Inspect token structure and claims; never paste active production tokens or secrets |
| Mockaroo | Synthetic data generator | https://www.mockaroo.com/ | Hosted service with a free allowance; confirm row/API limits on its pricing page | Generate synthetic JSON, CSV and SQL fixtures; use fake data only |
| Faker | Programmatic fake-data library | https://fakerjs.dev/ | MIT | Generate realistic synthetic test records in code; seed generation for repeatable tests |

### Forms, submissions, and feedback services

These are hosted form products. They are not substitutes for the open-source form-state libraries listed above, and their free plans are subject to provider quotas and terms.

| Name | Category | Actual site / docs / pricing | Verified free-plan information | UFME use and cautions |
|------|----------|-----------------------------|--------------------------------|-----------------------|
| FabForm | Form builder and submission service | https://fabform.io/ ; https://fabform.io/pricing/ | Official pricing page currently advertises a $0 plan with unlimited forms and responses, but several branding/customization features are excluded | Quick conversational forms, surveys, embeds and form endpoints; verify retention, data export and terms |
| Form.taxi | HTML form backend | https://form.taxi/en/plans ; https://docs.form.taxi/en/ | Official page lists a free plan with 3 forms and 40 submissions | Add submission handling to static HTML forms; verify data location, retention and privacy obligations |
| Formcarry | Form backend / endpoint | https://formcarry.com/ ; https://formcarry.com/pricing | Official pricing page lists a $0 plan with 1 form and 50 submissions per month | Receive HTML/JavaScript form submissions without building a backend; assess spam controls and file-upload restrictions |
| Formester | Form builder / surveys | https://formester.com/ ; https://formester.com/pricing/ | Official pricing page lists 10 forms and 100 responses per month on Free | Build embedded forms, surveys and quizzes; confirm whether needed logic/integrations require a paid tier |
| Forminit | Headless form backend | https://forminit.com/ ; https://forminit.com/pricing/ | Official pricing page lists 100 submissions per month on Free | Form handling, validation, spam protection, uploads and notifications; evaluate the vendor as a processor of submitted data |
| FormKeep | Form endpoint and builder | https://formkeep.com/ ; https://formkeep.com/features/pricing | Official pricing page lists unlimited forms and 50 submissions per month on Free | Contact forms, notifications and integrations; free plan has limited retention |
| Form Plume | HTML form backend | https://formplume.com/ | Official site advertises 500 submissions per month free | Simple HTML form endpoint, notifications, spam filtering and webhooks; confirm retention and terms |
| FluidForms | AI-assisted intake forms | https://fluidforms.ai/ ; https://fluidforms.ai/pricing | Official pricing page lists 100 responses/month and 10 AI actions on Free | Conditional intake and document workflows; avoid sensitive or regulated submissions unless required contractual and compliance terms are confirmed |
| Feedback Fish | Website feedback widget | https://feedback.fish/ | Provider advertises a no-card free start; verify current submission quota | Collect issue reports, ideas and compliments from a website; review identity, retention and export behavior |

### Visual testing, performance, and website capture

| Name | Category | Actual site / docs / pricing | Open-source / free-plan status | UFME use and cautions |
|------|----------|-----------------------------|-------------------------------|-----------------------|
| Argos | Visual regression and snapshot testing | https://argos-ci.com/ ; https://argos-ci.com/integrations ; https://argos-ci.com/pricing | Open-source SDKs/CLI with a free Hobby plan; official page lists up to 5,000 screenshots/month and permits commercial use | Evaluate screenshot diffs in CI. UFME should keep Selenium as its browser driver and prototype a CLI screenshot-upload flow before adopting Argos; do not introduce Playwright |
| GTmetrix | Website performance analysis | https://gtmetrix.com/ | Hosted service with free access and paid tiers; verify current test quotas | Supplement Lighthouse/Web Vitals with external waterfall and performance reports; test public deployments only |
| Microlink | Screenshot, metadata and page-rendering API | https://microlink.io/api ; https://microlink.io/docs/api/parameters/screenshot ; https://microlink.io/pricing | Hosted API; official pages list 25 free requests/day without an API key | Capture full-page or element screenshots and extract metadata for audits; send only public URLs and never put paid API keys in frontend code |
| Codacy | Static analysis / code quality | https://www.codacy.com/ ; https://www.codacy.com/pricing | Hosted platform; official pricing shows a free Developer IDE plugin and a free offering for open-source projects | Add code-quality/security feedback to review workflows; check repository privacy and coverage before connecting a private project |
| Counter | Privacy-focused web analytics | https://counter.dev/ | Open-source under AGPL-3.0; hosted service is free/pay-what-you-want | Lightweight cookie-free analytics; self-hosting and AGPL obligations should be reviewed before embedding |

### Hosting and deployment

| Name | Category | Actual site / docs / pricing | Free plan / constraints | UFME use and cautions |
|------|----------|-----------------------------|------------------------|-----------------------|
| Cloudflare Pages | Static and full-stack web deployment | https://developers.cloudflare.com/pages/ ; https://developers.cloudflare.com/pages/functions/pricing/ | Free plan available; static asset requests are free, while Functions use Workers quotas | Deploy previews and static frontends; for new full-stack projects review the current Workers recommendation and Functions limits |
| Netlify | Frontend hosting and CI deploys | https://www.netlify.com/ ; https://www.netlify.com/pricing/ | Current pricing page lists a $0 Free plan with 300 monthly credits; usage is credit-metered | Deploy static/modern framework sites and preview branches; monitor credits because builds, bandwidth, functions and requests consume them |
| GitHub Pages | Static-site hosting | https://docs.github.com/en/pages | Available for eligible GitHub repository plans; see official limits and usage policy | Host docs, portfolios and static project pages; not a general backend or dynamic application host |

### Selection rules for discovered services

1. Keep **open-source packages**, **open-source self-hosted applications**, **hosted SaaS**, and **browser-only utilities** in separate classes. Never infer that a free plan means an open-source license.
2. Follow the official site to the source repository, package registry, license, docs and pricing page. Record the exact package/product edition.
3. Capture the date when a free-tier quota is checked. Re-check quotas, inactivity rules, retention, deployment limits, bandwidth, seats and payment requirements before each project.
4. For external form endpoints, assess privacy policy, data residency, retention/deletion, export, spam defenses, abuse controls and any data-processing agreement. Do not send sensitive or regulated data to an unapproved provider.
5. Browser utilities that accept arbitrary text/JSON/tokens must be treated as external data processors unless their official docs establish local-only processing. Use synthetic data and never paste credentials, JWTs, private source, or customer records.
6. Use accessibility tools as evidence aids, not automatic conformance certification. Combine automated results with keyboard, screen-reader and human review.
7. For visual testing, keep Selenium WebDriver as UFME's browser automation standard. Integrate third-party visual systems through a verified CLI or supported WebDriver path; do not silently introduce Playwright.
8. Do not select a provider based only on a directory listing or marketing claim. Run a small proof of concept and document limitations before approval.

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
